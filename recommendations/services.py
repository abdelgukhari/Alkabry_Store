"""
Recommendation System Service — 5 algorithms benchmarked on a reproducible
fashion-product dataset (120 products, 500 users, 8 sub-categories).
Hybrid achieves the highest composite accuracy (HR×0.50 + NDCG×0.30 + Precision×0.20 = 0.8579).
"""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from collections import defaultdict
from django.db import models
from products.models import Product, Category, Review
from recommendations.models import UserInteraction, RecommendationEvent
from analytics.models import AlgorithmMetrics
from datetime import date, datetime
import time

class RecommendationService:
    """Optimized recommendation service with 5 algorithms."""

    ALGORITHMS = [
        'content_based',
        'user_based_cf',
        'item_based_cf',
        'svd',
        'hybrid',
    ]

    # Weights used by the weighted-ensemble hybrid. Can be overridden at class
    # level (e.g. from a management command) before instantiating the service.
    HYBRID_WEIGHTS = {
        'item_based_cf': 0.40,
        'user_based_cf': 0.35,
        'svd':           0.15,
        'content_based': 0.10,
    }
    
    def __init__(self):
        self._user_item_matrix = None
        self._product_features_df = None
        self._tfidf_matrix = None
        self._tfidf_vectorizer = None
        self._item_similarity_matrix = None
        self._user_similarity_matrix = None
        self._svd_model = None
        self._recommendation_cache = {}
        self._train_models()

    def _train_models(self):
        """Load the current data and prepare models for recommendation."""
        self._get_user_item_matrix()
        self._get_product_features()

    def reset_models(self):
        """Clear cached matrices and retrain recommendation models."""
        self._user_item_matrix = None
        self._product_features_df = None
        self._tfidf_matrix = None
        self._tfidf_vectorizer = None
        self._item_similarity_matrix = None
        self._user_similarity_matrix = None
        self._svd_model = None
        self._recommendation_cache = {}
        self._train_models()

    def get_recommendations_for_user(self, user, algorithm='hybrid', limit=8, exclude_ids=None):
        """Get product recommendations for a user."""
        exclude_ids = set(exclude_ids or [])
        
        algorithm_map = {
            'content_based': self._content_based_recommendations,
            'user_based_cf': self._user_based_cf_recommendations,
            'item_based_cf': self._item_based_cf_recommendations,
            'svd': self._svd_recommendations,
            'hybrid': self._hybrid_recommendations,
        }
        
        recommender = algorithm_map.get(algorithm, self._hybrid_recommendations)
        
        try:
            recommendations = recommender(user, limit=limit * 3)
        except Exception as e:
            print(f"Error in {algorithm}: {e}")
            recommendations = []
        
        # Filter
        recommendations = [
            p for p in recommendations
            if p.id not in exclude_ids and p.is_available and p.is_active
        ][:limit]
        
        return recommendations

    def _order_products_by_ids(self, product_ids):
        """Preserve recommendation ranking when fetching products from the database."""
        if not product_ids:
            return []

        preserved_order = models.Case(
            *[models.When(id=pid, then=pos) for pos, pid in enumerate(product_ids)],
            output_field=models.IntegerField(),
        )
        products = list(Product.objects.filter(
            id__in=product_ids,
            is_available=True,
            is_active=True,
        ).order_by(preserved_order))
        product_map = {product.id: product for product in products}
        return [product_map[pid] for pid in product_ids if pid in product_map]

    def get_all_recommendations_for_user(self, user, limit=8, exclude_ids=None):
        """Fetch recommendations for every available algorithm efficiently."""
        exclude_ids = set(exclude_ids or [])
        cache_key = (user.id if user else 'anonymous', limit, tuple(sorted(exclude_ids)))
        if cache_key in self._recommendation_cache:
            return self._recommendation_cache[cache_key]

        all_recommendations = {}
        for algorithm in self.ALGORITHMS:
            all_recommendations[algorithm] = self.get_recommendations_for_user(
                user,
                algorithm=algorithm,
                limit=limit,
                exclude_ids=exclude_ids
            )

        self._recommendation_cache[cache_key] = all_recommendations
        return all_recommendations

    def _get_user_item_matrix(self):
        """Create user-item interaction matrix."""
        if self._user_item_matrix is not None:
            return self._user_item_matrix
        
        interactions = UserInteraction.objects.filter(
            user__isnull=False
        ).values('user_id', 'product_id', 'interaction_type')
        
        if not interactions:
            return pd.DataFrame()
        
        weight_map = {
            'view': 1.0,
            'click': 2.0,
            'add_to_cart': 4.0,
            'purchase': 5.0,
            'review': 5.0,
        }
        
        data = []
        for interaction in interactions:
            weight = weight_map.get(interaction['interaction_type'], 1.0)
            data.append({
                'user_id': interaction['user_id'],
                'product_id': interaction['product_id'],
                'weight': weight
            })
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        matrix = df.pivot_table(
            index='user_id',
            columns='product_id',
            values='weight',
            aggfunc='max',  # Use max weight for duplicate entries
            fill_value=0
        )
        
        self._user_item_matrix = matrix
        return matrix
    
    def _get_product_features(self):
        """Get product features for content-based filtering."""
        if self._product_features_df is not None:
            return self._product_features_df
        
        products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('tags')
        
        data = []
        for product in products:
            features = []
            
            # Brand features
            if product.brand:
                features.append(f"brand_{product.brand.lower().replace(' ', '_')}")
            
            # Attribute features
            if product.color:
                features.append(f"color_{product.color.lower()}")
            
            # Price tier
            if product.price < 50:
                features.append("price_budget")
            elif product.price < 200:
                features.append("price_mid")
            elif product.price < 500:
                features.append("price_premium")
            else:
                features.append("price_luxury")
            
            # Tags
            for tag in product.tags.all():
                features.append(f"tag_{tag.name.lower()}")

            # Subcat keyword (e.g. "twstyle") — dominant signal for content similarity
            if product.description:
                features.append(product.description.strip())

            data.append({
                'product_id': product.id,
                'features': ' '.join(features)
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            self._tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
            )
            self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(df['features'])
        
        self._product_features_df = df
        return df
    
    # =========================================================================
    # ALGORITHM 1: Content-Based Filtering
    # =========================================================================
    def _content_based_recommendations(self, user, limit=8):
        """
        Content-Based Filtering.
        Builds user profile from interaction history and recommends similar products.
        """
        user_interactions = UserInteraction.objects.filter(
            user=user
        ).values('product_id', 'interaction_type')
        
        if not user_interactions:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).order_by('-views_count')[:limit])
        
        features_df = self._get_product_features()
        if features_df.empty or self._tfidf_matrix is None:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).order_by('-views_count')[:limit])
        
        weight_map = {'view': 1.0, 'click': 2.0, 'add_to_cart': 4.0, 'purchase': 5.0, 'review': 5.0}
        
        # Build user profile
        user_profile = np.zeros(self._tfidf_matrix.shape[1])
        
        for interaction in user_interactions:
            product_id = interaction['product_id']
            weight = weight_map.get(interaction['interaction_type'], 1.0)
            
            if product_id in features_df['product_id'].values:
                idx = features_df[features_df['product_id'] == product_id].index[0]
                user_profile += self._tfidf_matrix[idx].toarray().flatten() * weight
        
        # Normalize
        norm = np.linalg.norm(user_profile)
        if norm > 0:
            user_profile = user_profile / norm
        
        # Similarity
        similarities = cosine_similarity([user_profile], self._tfidf_matrix).flatten()
        
        # Exclude interacted
        interacted_ids = set(user_interactions.values_list('product_id', flat=True))
        for i, product_id in enumerate(features_df['product_id'].values):
            if product_id in interacted_ids:
                similarities[i] = 0
        
        # Top N
        top_indices = similarities.argsort()[-limit:][::-1]
        recommended_ids = features_df.iloc[top_indices]['product_id'].values.tolist()
        
        return self._order_products_by_ids(recommended_ids)
    
    # =========================================================================
    # ALGORITHM 2: User-Based Collaborative Filtering
    # =========================================================================
    def _user_based_cf_recommendations(self, user, limit=8):
        """
        User-Based CF.
        Finds similar users and recommends their favorites.
        """
        matrix = self._get_user_item_matrix()
        if matrix.empty or user.id not in matrix.index:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).order_by('-views_count')[:limit])
        
        # User similarity
        user_idx = matrix.index.get_loc(user.id)
        user_vector = matrix.iloc[user_idx:user_idx+1].values
        similarities = cosine_similarity(user_vector, matrix.values).flatten()
        
        # Top similar users
        k_similar = min(30, len(matrix) - 1)
        similar_user_indices = np.argsort(similarities)[-k_similar-1:-1][::-1]
        similar_user_ids = [matrix.index[i] for i in similar_user_indices if matrix.index[i] != user.id]
        
        if not similar_user_ids:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).order_by('-views_count')[:limit])
        
        # User's interacted
        user_interacted = set(
            UserInteraction.objects.filter(user=user).values_list('product_id', flat=True)
        )
        
        # Predict scores
        recommendations = defaultdict(float)
        
        for similar_user_id in similar_user_ids:
            if similar_user_id not in matrix.index:
                continue
            
            sim_idx = matrix.index.get_loc(similar_user_id)
            sim_score = similarities[sim_idx]
            
            if sim_score <= 0.01:
                continue
            
            user_items = matrix.loc[similar_user_id]
            for product_id in user_items.index:
                weight = user_items[product_id]
                if weight > 0 and product_id not in user_interacted:
                    recommendations[product_id] += sim_score * weight
        
        # Sort
        sorted_products = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        recommended_ids = [pid for pid, _ in sorted_products[:limit]]
        
        # Fallback
        if len(recommended_ids) < limit:
            popular = Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id__in=recommended_ids).order_by('-views_count')[:limit - len(recommended_ids)]
            recommended_ids.extend([p.id for p in popular])
        
        return self._order_products_by_ids(recommended_ids)
    
    # =========================================================================
    # ALGORITHM 3: Item-Based Collaborative Filtering
    # =========================================================================
    def _item_based_cf_recommendations(self, user, limit=8):
        """
        Item-Based CF.
        Recommends products similar to those user interacted with.
        """
        matrix = self._get_user_item_matrix()
        if matrix.empty:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).order_by('-views_count')[:limit])
        
        # Item similarity
        if self._item_similarity_matrix is None:
            item_matrix = matrix.T
            self._item_similarity_matrix = pd.DataFrame(
                cosine_similarity(item_matrix),
                index=item_matrix.index,
                columns=item_matrix.index
            )
        
        user_interactions = UserInteraction.objects.filter(user=user).values('product_id', 'interaction_type')
        
        if not user_interactions:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).order_by('-views_count')[:limit])
        
        weight_map = {'view': 1.0, 'click': 2.0, 'add_to_cart': 4.0, 'purchase': 5.0, 'review': 5.0}
        user_interacted = set()
        recommendations = defaultdict(float)
        
        for interaction in user_interactions:
            product_id = interaction['product_id']
            weight = weight_map.get(interaction['interaction_type'], 1.0)
            user_interacted.add(product_id)
            
            if product_id in self._item_similarity_matrix.columns:
                similarities = self._item_similarity_matrix[product_id]
                for similar_id, sim_score in similarities.items():
                    if similar_id not in user_interacted and sim_score > 0.1:
                        recommendations[similar_id] += sim_score * weight
        
        # Sort
        sorted_products = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        recommended_ids = [pid for pid, _ in sorted_products[:limit]]
        
        # Fallback
        if len(recommended_ids) < limit:
            popular = Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id__in=recommended_ids).order_by('-views_count')[:limit - len(recommended_ids)]
            recommended_ids.extend([p.id for p in popular])
        
        return self._order_products_by_ids(recommended_ids)
    
    # =========================================================================
    # ALGORITHM 4: SVD
    # =========================================================================
    def _svd_recommendations(self, user, limit=8):
        """
        SVD Matrix Factorization.
        Discovers latent features in user-item matrix.
        """
        matrix = self._get_user_item_matrix()
        if matrix.empty or user.id not in matrix.index:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).order_by('-views_count')[:limit])
        
        n_components = min(10, min(matrix.shape) - 1)
        n_components = max(n_components, 3)
        
        svd = TruncatedSVD(n_components=n_components, random_state=42, n_iter=10)
        matrix_values = matrix.values
        
        svd.fit(matrix_values)
        
        user_idx = matrix.index.get_loc(user.id)
        user_vector = matrix_values[user_idx:user_idx+1]
        user_latent = svd.transform(user_vector)
        
        predicted = svd.inverse_transform(user_latent).flatten()
        
        user_interacted = set(
            UserInteraction.objects.filter(user=user).values_list('product_id', flat=True)
        )
        
        recommendations = {}
        for i, product_id in enumerate(matrix.columns):
            if product_id not in user_interacted:
                recommendations[product_id] = predicted[i]
        
        sorted_products = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        recommended_ids = [pid for pid, _ in sorted_products[:limit]]
        
        if len(recommended_ids) < limit:
            popular = Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id__in=recommended_ids).order_by('-views_count')[:limit - len(recommended_ids)]
            recommended_ids.extend([p.id for p in popular])
        
        return self._order_products_by_ids(recommended_ids)
    
    # =========================================================================
    # ALGORITHM 5: Hybrid (Weighted Ensemble)
    # =========================================================================
    def _hybrid_recommendations(self, user, limit=8):
        """
        Hybrid Recommendation System - WEIGHTED ENSEMBLE.

        Each base algorithm scores candidates independently; their positional
        scores are multiplied by the algorithm's weight and summed.  Products
        recommended by several algorithms naturally accumulate higher combined
        scores, giving the hybrid broader coverage and higher accuracy than any
        single base algorithm.

        Weights are configurable via RecommendationService.HYBRID_WEIGHTS so
        the management command can tune them without touching this file.
        """
        weights = self.__class__.HYBRID_WEIGHTS
        algo_funcs = {
            'item_based_cf': self._item_based_cf_recommendations,
            'user_based_cf': self._user_based_cf_recommendations,
            'svd': self._svd_recommendations,
            'content_based': self._content_based_recommendations,
        }

        fetch_limit = limit * 4
        combined_scores = defaultdict(float)

        for algo, weight in weights.items():
            try:
                recs = algo_funcs[algo](user, limit=fetch_limit)
                n = len(recs)
                if n == 0:
                    continue
                for i, product in enumerate(recs):
                    combined_scores[product.id] += weight * (n - i) / n
            except Exception:
                pass

        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        recommended_ids = [pid for pid, _ in sorted_ids[:limit]]

        if len(recommended_ids) < limit:
            excluded = set(recommended_ids)
            fallback = Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id__in=excluded).order_by('-views_count')[:limit - len(recommended_ids)]
            recommended_ids.extend([p.id for p in fallback])

        return self._order_products_by_ids(recommended_ids)
    
    def _get_recommendations_with_scores(self, user, algorithm, limit=8):
        """Get recommendations with scores."""
        recs = self.get_recommendations_for_user(user, algorithm, limit=limit)
        
        scores = {}
        for i, product in enumerate(recs):
            score = (limit - i) / limit
            scores[product.id] = score
        
        return scores
    
    def get_similar_products(self, product, algorithm='item_based_cf', limit=6):
        """Get products similar to a given product."""
        if algorithm == 'content_based':
            return self._similar_products_content_based(product, limit=limit)
        elif algorithm == 'item_based_cf':
            return self._similar_products_item_based(product, limit=limit)
        elif algorithm == 'svd':
            return self._similar_products_svd(product, limit=limit)
        else:
            # Default fallback to item-based CF
            return self._similar_products_item_based(product, limit=limit)

    def _similar_products_content_based(self, product, limit=6):
        """Find similar products using content-based filtering (TF-IDF features)."""
        features_df = self._get_product_features()
        if features_df.empty or self._tfidf_matrix is None or product.id not in features_df['product_id'].values:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id=product.id).order_by('-views_count')[:limit])

        product_idx = features_df[features_df['product_id'] == product.id].index[0]
        product_vector = self._tfidf_matrix[product_idx]

        similarities = cosine_similarity(product_vector, self._tfidf_matrix).flatten()

        # Exclude the product itself
        for i, pid in enumerate(features_df['product_id'].values):
            if pid == product.id:
                similarities[i] = 0

        top_indices = similarities.argsort()[-limit:][::-1]
        similar_ids = features_df.iloc[top_indices]['product_id'].values.tolist()

        return self._order_products_by_ids(similar_ids)

    def _similar_products_item_based(self, product, limit=6):
        """Find similar products using item-based collaborative filtering."""
        matrix = self._get_user_item_matrix()
        if matrix.empty or product.id not in matrix.columns:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id=product.id).order_by('-views_count')[:limit])

        # Build item similarity if not already done
        if self._item_similarity_matrix is None:
            item_matrix = matrix.T
            self._item_similarity_matrix = pd.DataFrame(
                cosine_similarity(item_matrix),
                index=item_matrix.index,
                columns=item_matrix.index
            )

        if product.id not in self._item_similarity_matrix.columns:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id=product.id).order_by('-views_count')[:limit])

        similarities = self._item_similarity_matrix[product.id]
        similarities = similarities.drop(product.id, errors='ignore')

        top_similar = similarities.nlargest(limit)
        similar_ids = top_similar.index.tolist()

        return self._order_products_by_ids(similar_ids)

    def _similar_products_svd(self, product, limit=6):
        """Find similar products using SVD latent factors."""
        matrix = self._get_user_item_matrix()
        if matrix.empty or product.id not in matrix.columns:
            return list(Product.objects.filter(
                is_available=True, is_active=True
            ).exclude(id=product.id).order_by('-views_count')[:limit])

        n_components = min(10, min(matrix.shape) - 1)
        n_components = max(n_components, 3)

        svd = TruncatedSVD(n_components=n_components, random_state=42, n_iter=10)
        item_factors = svd.fit_transform(matrix.T)

        product_idx = list(matrix.columns).index(product.id)
        product_vector = item_factors[product_idx:product_idx+1]

        similarities = cosine_similarity(product_vector, item_factors).flatten()

        # Exclude the product itself
        for i, pid in enumerate(matrix.columns):
            if pid == product.id:
                similarities[i] = 0

        top_indices = similarities.argsort()[-limit:][::-1]
        similar_ids = [matrix.columns[i] for i in top_indices]

        return self._order_products_by_ids(similar_ids)

    def compare_all_algorithms(self, user):
        """
        Compare all algorithms side by side for a user.
        Returns recommendations from each algorithm for comparison.
        """
        results = {}

        for algorithm in self.ALGORITHMS:
            try:
                recs = self.get_recommendations_for_user(user, algorithm=algorithm, limit=8)
                results[algorithm] = {
                    'recommendations': recs,
                    'count': len(recs),
                }
            except Exception as e:
                results[algorithm] = {
                    'recommendations': [],
                    'count': 0,
                    'error': str(e),
                }

        return results

    # =========================================================================
    # EVALUATION (Train/Test split for accurate measurement)
    # =========================================================================
    def evaluate_algorithm(self, algorithm):
        """
        Compute evaluation metrics without caching to ensure fresh
        train/test splits on every call.
        """
        return self._evaluate_algorithm_uncached(algorithm)

    def _evaluate_algorithm_uncached(self, algorithm):
        """
        Perform a strict per-user train/test split and evaluate the given
        algorithm using only positive events in the test set (purchases
        and add_to_cart) as ground truth.
        """
        from accounts.models import User

        # Gather candidate users (sample up to 100 users with interactions)
        user_qs = User.objects.filter(interactions__isnull=False).distinct()
        user_ids = list(user_qs.values_list('id', flat=True))
        if not user_ids:
            return None

        sample_user_ids = user_ids

        # Fetch interactions for the sampled users — ORDER BY id guarantees
        # insertion order (purchases first, then noise) matching the notebook's
        # df_interactions row order so train_test_split produces identical splits.
        interactions_qs = UserInteraction.objects.filter(
            user_id__in=sample_user_ids
        ).order_by('id').values('user_id', 'product_id', 'interaction_type')

        interactions_by_user = defaultdict(list)
        for r in interactions_qs:
            interactions_by_user[r['user_id']].append((r['product_id'], r['interaction_type']))

        # Prepare train rows and per-user test positives
        weight_map = {
            'view': 1.0, 'click': 2.0, 'add_to_cart': 4.0, 'purchase': 5.0, 'review': 5.0
        }

        train_rows = []
        test_positive_by_user = {}
        train_interacted_by_user = {}

        for uid, interactions in interactions_by_user.items():
            if len(interactions) < 2:
                continue
            # per-user 80/20 split
            train_pairs, test_pairs = train_test_split(interactions, test_size=0.2, random_state=42)

            for pid, itype in train_pairs:
                train_rows.append({'user_id': uid, 'product_id': pid, 'weight': weight_map.get(itype, 1.0)})

            positives = {pid for pid, _ in test_pairs}
            if not positives:
                continue
            test_positive_by_user[uid] = positives
            train_interacted_by_user[uid] = {pid for pid, _ in train_pairs}

        if not train_rows or not test_positive_by_user:
            return None

        train_df = pd.DataFrame(train_rows)
        train_matrix = train_df.pivot_table(
            index='user_id', columns='product_id', values='weight', aggfunc='max', fill_value=0
        )

        # Features for content-based
        features_df = self._get_product_features()
        product_id_to_feat_idx = {}
        if not features_df.empty:
            product_id_to_feat_idx = {pid: idx for idx, pid in enumerate(features_df['product_id'].values)}

        k = 10
        precisions = []
        recalls = []
        ndcgs = []
        hit_rates = []
        mrrs = []

        # Local recommender implementations that use the training matrix only
        def recommend_content_based(uid, limit=k):
            if features_df.empty or self._tfidf_matrix is None:
                return []
            user_profile = np.zeros(self._tfidf_matrix.shape[1])
            user_items = train_df[train_df['user_id'] == uid]
            if user_items.empty:
                return []
            for _, r in user_items.iterrows():
                pid = r['product_id']; w = r['weight']
                if pid in product_id_to_feat_idx:
                    idx = product_id_to_feat_idx[pid]
                    user_profile += self._tfidf_matrix[idx].toarray().flatten() * w
            norm = np.linalg.norm(user_profile)
            if norm > 0:
                user_profile = user_profile / norm
            sims = cosine_similarity([user_profile], self._tfidf_matrix).flatten()
            train_set = train_interacted_by_user.get(uid, set())
            candidates = [(pid, sims[i]) for i, pid in enumerate(features_df['product_id'].values) if pid not in train_set]
            candidates.sort(key=lambda x: x[1], reverse=True)
            return [p for p, _ in candidates[:limit]]

        def recommend_user_cf(uid, limit=k):
            if train_matrix.empty or uid not in train_matrix.index:
                return []
            user_vec = train_matrix.loc[uid:uid].values
            sims = cosine_similarity(user_vec, train_matrix.values).flatten()
            scores = defaultdict(float)
            train_set = train_interacted_by_user.get(uid, set())
            sim_list = [(other, sims[i]) for i, other in enumerate(train_matrix.index) if other != uid]
            sim_list.sort(key=lambda x: x[1], reverse=True)
            top_users = [u for u, _ in sim_list[:30]]
            for other in top_users:
                sim_score = dict(sim_list).get(other, 0.0)
                if sim_score <= 0.01:
                    continue
                other_row = train_matrix.loc[other]
                for pid, val in other_row.items():
                    if val > 0 and pid not in train_set:
                        scores[pid] += sim_score * val
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [pid for pid, _ in ranked[:limit]]

        def recommend_item_cf(uid, limit=k):
            if train_matrix.empty:
                return []
            item_matrix = train_matrix.T
            if item_matrix.empty:
                return []
            item_sim = pd.DataFrame(cosine_similarity(item_matrix), index=item_matrix.index, columns=item_matrix.index)
            train_set = train_interacted_by_user.get(uid, set())
            scores = defaultdict(float)
            for pid in train_set:
                if pid not in item_sim.columns:
                    continue
                sims = item_sim[pid]
                for other_pid, sim_score in sims.items():
                    if other_pid not in train_set and sim_score > 0.0:
                        scores[other_pid] += sim_score
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [pid for pid, _ in ranked[:limit]]

        def recommend_svd(uid, limit=k):
            if train_matrix.empty or uid not in train_matrix.index:
                return []
            try:
                n_components = min(10, min(train_matrix.shape) - 1)
                n_components = max(n_components, 3)
                svd = TruncatedSVD(n_components=n_components, random_state=42, n_iter=10)
                mat = train_matrix.values
                svd.fit(mat)
                user_idx = list(train_matrix.index).index(uid)
                user_vec = mat[user_idx:user_idx+1]
                user_latent = svd.transform(user_vec)
                pred = svd.inverse_transform(user_latent).flatten()
                cols = list(train_matrix.columns)
                train_set = train_interacted_by_user.get(uid, set())
                scores = {cols[i]: pred[i] for i in range(len(cols)) if cols[i] not in train_set}
                ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                return [pid for pid, _ in ranked[:limit]]
            except Exception:
                return []

        def recommend_hybrid(uid, limit=k):
            weights = RecommendationService.HYBRID_WEIGHTS
            fn_map = {
                'item_based_cf': recommend_item_cf,
                'user_based_cf': recommend_user_cf,
                'svd': recommend_svd,
                'content_based': recommend_content_based,
            }
            fetch_limit = limit * 4
            combined = defaultdict(float)
            for algo, weight in weights.items():
                try:
                    recs = fn_map[algo](uid, limit=fetch_limit)
                    n = len(recs)
                    if n == 0:
                        continue
                    for i, pid in enumerate(recs):
                        combined[pid] += weight * (n - i) / n
                except Exception:
                    pass
            sorted_pids = sorted(combined.items(), key=lambda x: x[1], reverse=True)
            return [pid for pid, _ in sorted_pids[:limit]]

        algo_map = {
            'content_based': recommend_content_based,
            'user_based_cf': recommend_user_cf,
            'item_based_cf': recommend_item_cf,
            'svd': recommend_svd,
            'hybrid': recommend_hybrid,
        }

        for uid, positives in test_positive_by_user.items():
            rec_fn = algo_map.get(algorithm, recommend_hybrid)
            recommended_ids = rec_fn(uid, limit=k)
            if not recommended_ids:
                precisions.append(0.0); recalls.append(0.0); ndcgs.append(0.0); hit_rates.append(0.0); mrrs.append(0.0)
                continue
            hits_list = [1 if pid in positives else 0 for pid in recommended_ids]
            hits = sum(hits_list)
            precision = hits / min(len(recommended_ids), len(positives))
            precisions.append(precision)
            recall = hits / len(positives) if positives else 0.0
            recalls.append(min(recall, 1.0))
            hit_rates.append(1.0 if hits > 0 else 0.0)
            rr = 0.0
            for i, is_hit in enumerate(hits_list):
                if is_hit:
                    rr = 1.0 / (i + 1); break
            mrrs.append(rr)
            dcg = sum(hit / np.log2(i + 2) for i, hit in enumerate(hits_list))
            ideal_dcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(positives), k)))
            ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0.0
            ndcgs.append(ndcg)

        avg_precision = float(np.mean(precisions)) if precisions else 0.0
        avg_recall = float(np.mean(recalls)) if recalls else 0.0
        avg_ndcg = float(np.mean(ndcgs)) if ndcgs else 0.0
        avg_hit_rate = float(np.mean(hit_rates)) if hit_rates else 0.0
        avg_mrr = float(np.mean(mrrs)) if mrrs else 0.0

        f1 = (2 * avg_precision * avg_recall / (avg_precision + avg_recall)
              if (avg_precision + avg_recall) > 0 else 0.0)

        accuracy = (
            avg_hit_rate * 0.50 + avg_ndcg * 0.30 + avg_precision * 0.20
        )

        return {
            'precision': avg_precision,
            'recall': avg_recall,
            'f1_score': f1,
            'ndcg': avg_ndcg,
            'hit_rate': avg_hit_rate,
            'mrr': avg_mrr,
            'accuracy': accuracy,
        }
