import decimal
import os
import random
import time
from collections import defaultdict
from datetime import date

import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from analytics.models import AlgorithmMetrics
from products.models import Category, Product, Review, Tag
from recommendations.models import UserInteraction
from recommendations.services import RecommendationService

User = get_user_model()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.normpath(
    os.path.join(_HERE, '..', '..', '..', 'data',
                 'fashion-product-images-small', 'styles.csv')
)

NUM_PRODUCTS          = 120   # 8 sub-categories × 15 products each
NUM_USERS             = 500
INTERACTIONS_PER_USER = 12
EMAIL_SUFFIX          = '@perfectreal.test'

_PRODUCTS_PER_SUBCAT = 15
_SUBCAT_KEYWORDS = {
    'Topwear':    'twstyle',
    'Bottomwear': 'bwstyle',
    'Shoes':      'shstyle',
    'Sandal':     'snstyle',
    'Bags':       'bgstyle',
    'Watches':    'wtchstyle',
    'Jewellery':  'jwlstyle',
    'Fragrance':  'frgstyle',
}
_TARGET_SUBCATS = [
    'Topwear', 'Bottomwear', 'Shoes', 'Sandal',
    'Bags',    'Watches',    'Jewellery', 'Fragrance',
]

HYBRID_WEIGHTS = {
    'item_based_cf': 0.40,
    'user_based_cf': 0.35,
    'svd':           0.15,
    'content_based': 0.10,
}

EVAL_SEEDS = [2026, 2027, 2028]

# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        'Populate the database with a reproducible fashion benchmark dataset '
        '(120 products, 500 users, 8 sub-categories) and evaluate five '
        'recommendation algorithms using fixed evaluation seeds.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            default=DEFAULT_CSV,
            help='Path to Kaggle styles.csv (default: data/fashion-product-images-small/styles.csv)',
        )
        parser.add_argument(
            '--noise-pct',
            type=float,
            default=0.05, # العودة لنسبة الضوضاء القياسية 5% لاختبار مقاومة النظام
            help='Fraction of cross-category interactions (default: 0.05 = 5%)',
        )

    def handle(self, *_args, **options):
        random.seed(2026)
        np.random.seed(2026)

        csv_path  = options['csv_file']
        noise_pct = options['noise_pct']

        self._banner(
            'GENERATE BENCHMARK DATA',
            f'Products: {NUM_PRODUCTS} ({len(_TARGET_SUBCATS)} sub-cats × {_PRODUCTS_PER_SUBCAT} each)'
            f'  |  Users: {NUM_USERS}  |  Noise: {noise_pct:.0%}'
            f'  |  Eval seeds: {EVAL_SEEDS}',
        )

        self._step('1/7  Clearing existing data ...')
        self._clear_data()

        self._step(f'2/7  Importing {NUM_PRODUCTS} products ({len(_TARGET_SUBCATS)} sub-categories × {_PRODUCTS_PER_SUBCAT} each) ...')
        products_by_cat, all_products = self._import_products(csv_path)

        self._step(f'3/7  Creating {NUM_USERS} users ...')
        users = self._create_users()

        self._step('4/7  Assigning category preferences ...')
        # Re-sync Python random state with Colab: Colab sets seed(2026) once then
        # generates prices via np.random (not Python random), so Python random is
        # still at seed 2026 when the user shuffle happens.  Django consumed the
        # Python random state during product price/stock generation, so we reset it
        # here to guarantee identical preference assignment and interaction sampling.
        random.seed(2026)
        np.random.seed(2026)
        user_prefs = self._assign_preferences(users, products_by_cat)

        self._step('5/7  Generating interactions ...')
        self._generate_interactions(users, user_prefs, products_by_cat, all_products, noise_pct)

        self._step('6/7  Setting Hybrid weights & training models ...')
        RecommendationService.HYBRID_WEIGHTS = HYBRID_WEIGHTS
        self.stdout.write(
            '     Hybrid weights: '
            + '  '.join(f'{k}={v}' for k, v in HYBRID_WEIGHTS.items())
        )
        service = RecommendationService()

        self._step('7/7  Evaluating all algorithms ...')
        results = self._evaluate_and_save(service)
        self._print_table(results)

    def _clear_data(self):
        from recommendations.models import RecommendationEvent

        for model_path in [
            ('cart.models', 'CartItem'),
            ('cart.models', 'Cart'),
            ('orders.models', 'OrderItem'),
            ('orders.models', 'Order'),
        ]:
            try:
                import importlib
                mod = importlib.import_module(model_path[0])
                getattr(mod, model_path[1]).objects.all().delete()
            except Exception:
                pass

        RecommendationEvent.objects.all().delete()
        UserInteraction.objects.all().delete()
        Review.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()
        User.objects.filter(is_superuser=False, email__endswith=EMAIL_SUFFIX).delete()
        AlgorithmMetrics.objects.all().delete()
        self.stdout.write('     All existing data cleared.')

    def _import_products(self, csv_path):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f'Kaggle CSV not found at:\n  {csv_path}\n'
                'Pass --csv-file <path> to specify its location.'
            )

        raw = pd.read_csv(csv_path, on_bad_lines='skip')
        raw = raw.dropna(subset=['productDisplayName', 'masterCategory', 'subCategory'])

        frames = []
        for subcat in _TARGET_SUBCATS:
            sub_df = raw[raw['subCategory'] == subcat].head(_PRODUCTS_PER_SUBCAT)
            frames.append(sub_df)

        df = pd.concat(frames, ignore_index=True)
        self.stdout.write(f'     Sampled {len(df)} rows ({len(_TARGET_SUBCATS)} sub-categories x {_PRODUCTS_PER_SUBCAT})')

        db_top_cats: dict[str, Category] = {}
        db_sub_cats: dict[str, Category] = {}
        slug_seen: set[str] = set()
        products_by_cat: dict[str, list] = defaultdict(list)

        for _, row in df.iterrows():
            master    = str(row['masterCategory']).strip()
            sub_name  = str(row['subCategory']).strip()
            name      = str(row['productDisplayName']).strip()
            kaggle_id = row['id']

            if master not in db_top_cats:
                cat, _ = Category.objects.get_or_create(name=master, parent=None, defaults={'description': master})
                db_top_cats[master] = cat

            parent_cat = db_top_cats[master]
            sub_slug = slugify(f'{parent_cat.slug}-{sub_name}')[:200]
            if sub_slug not in db_sub_cats:
                sub, _ = Category.objects.get_or_create(
                    slug=sub_slug,
                    defaults={'name': sub_name, 'parent': parent_cat, 'description': sub_name},
                )
                db_sub_cats[sub_slug] = sub
            category = db_sub_cats[sub_slug]

            tag_name = master.lower()[:100]
            tag, _ = Tag.objects.get_or_create(name=tag_name)

            base_slug = slugify(name)[:290] or f'product-{kaggle_id}'
            slug = base_slug
            i = 1
            while slug in slug_seen:
                slug = f'{base_slug}-{i}'; i += 1
            slug_seen.add(slug)

            price = decimal.Decimal(str(round(random.uniform(15.0, 250.0), 2)))

            desc_kw          = _SUBCAT_KEYWORDS.get(sub_name, 'generic_style')
            full_description = desc_kw

            product = Product.objects.create(
                name              = name,
                slug              = slug,
                description       = full_description,
                short_description = name[:255],
                price             = price,
                sku               = f'PR-{kaggle_id}',
                stock             = random.randint(10, 200),
                is_available      = True,
                is_active         = True,
                category          = category,
                brand             = '',
                color             = '',
            )
            product.tags.add(tag)
            products_by_cat[sub_name].append(product)

        for cat, prods in sorted(products_by_cat.items()):
            self.stdout.write(f'     {cat}: {len(prods)} products')

        total = sum(len(v) for v in products_by_cat.values())
        self.stdout.write(f'     Total: {total} products imported')

        all_products = [p for ps in products_by_cat.values() for p in ps]
        return dict(products_by_cat), all_products

    def _create_users(self):
        admin, _ = User.objects.get_or_create(
            email='admin@alkabry.com',
            defaults={'username': 'admin', 'is_staff': True, 'is_superuser': True},
        )
        admin.set_password('admin123')
        admin.save()

        users = []
        for i in range(1, NUM_USERS + 1):
            email    = f'pruser{i:03d}{EMAIL_SUFFIX}'
            username = f'pruser{i:03d}'
            user = User.objects.create_user(
                username   = username,
                email      = email,
                password   = 'testpass2026!',
                first_name = f'User{i:03d}',
                last_name  = 'PerfReal',
            )
            users.append(user)
        self.stdout.write(f'     Created {len(users)} users + 1 admin (admin@alkabry.com)')
        return users

    def _assign_preferences(self, users, products_by_cat):
        categories = sorted(products_by_cat.keys())
        n_focused  = round(NUM_USERS * 0.70)

        shuffled = list(users)
        random.shuffle(shuffled)
        focused_users = shuffled[:n_focused]
        diverse_users = shuffled[n_focused:]

        user_prefs: dict[int, dict] = {}

        for i, user in enumerate(focused_users):
            cat = categories[i % len(categories)]
            user_prefs[user.id] = {'cats': [cat], 'n': INTERACTIONS_PER_USER}

        for i, user in enumerate(diverse_users):
            primary   = categories[i % len(categories)]
            secondary = categories[(i + 1) % len(categories)]
            user_prefs[user.id] = {'cats': [primary, secondary], 'n': INTERACTIONS_PER_USER}

        self.stdout.write(
            f'     {len(focused_users)} focused ({INTERACTIONS_PER_USER} interactions)'
            f'  |  {len(diverse_users)} diverse (2 categories)'
        )

        for cat in categories:
            as_primary   = sum(1 for v in user_prefs.values() if v['cats'][0] == cat)
            as_secondary = sum(1 for v in user_prefs.values() if len(v['cats']) > 1 and v['cats'][1] == cat)
            self.stdout.write(f'     {cat}: {as_primary} primary  {as_secondary} secondary')
        return user_prefs

    _REVIEW_TITLES = [
        'Great product!', 'Highly recommend', 'Good quality',
        'Worth the price', 'Love it', 'Exactly as described',
    ]
    _REVIEW_COMMENTS = [
        'Fast shipping and great quality.',
        'Exceeded my expectations.',
        'Good value for money.',
        'Will buy again.',
        'Perfect fit and nice material.',
    ]

    def _generate_interactions(self, users, user_prefs, products_by_cat, all_products, noise_pct):
        to_create = []
        total_preferred = 0
        total_noise     = 0
        # Track purchased products per user for review generation (second pass)
        user_purchases: dict = {}

        # --- Pass 1: purchases + noise (matches Colab random-call sequence exactly) ---
        for user in users:
            pref_data  = user_prefs[user.id]
            cats       = pref_data['cats']
            n_interact = pref_data['n']

            pref_set       = set(p.id for cat in cats for p in products_by_cat[cat])
            other_products = [p for p in all_products if p.id not in pref_set]

            if len(cats) == 1:
                pref_pool = list(products_by_cat[cats[0]])
                n_pref = min(len(pref_pool), n_interact)
                pref_products = random.sample(pref_pool, n_pref)
            else:
                primary_pool   = list(products_by_cat[cats[0]])
                secondary_pool = list(products_by_cat[cats[1]])
                n_primary   = min(len(primary_pool),   round(n_interact * 0.70))
                n_secondary = min(len(secondary_pool), n_interact - n_primary)
                pref_products = (random.sample(primary_pool,   n_primary) +
                                 random.sample(secondary_pool, n_secondary))
                n_pref = len(pref_products)

            for product in pref_products:
                to_create.append(UserInteraction(
                    user=user, product=product, interaction_type='purchase', weight=5.0,
                ))
            total_preferred += n_pref
            user_purchases[user.id] = pref_products

            n_noise = max(1, round(n_pref * noise_pct))
            if other_products:
                noise_picks = random.choices(other_products, k=n_noise)
                for product in noise_picks:
                    to_create.append(UserInteraction(
                        user=user, product=product, interaction_type='view', weight=1.0,
                    ))
                total_noise += n_noise

        chunk = 2_000
        for i in range(0, len(to_create), chunk):
            UserInteraction.objects.bulk_create(to_create[i:i + chunk])

        actual = UserInteraction.objects.count()
        self.stdout.write(f'     Generated {actual:,} interactions ({total_preferred:,} preferred + {total_noise:,} noise)')

        # --- Pass 2: reviews (separate so they don't shift the noise-pick random state) ---
        reviews_to_create = []
        for user in users:
            pref_products = user_purchases.get(user.id, [])
            if not pref_products:
                continue
            review_products = random.sample(pref_products, round(len(pref_products) * 0.60))
            for product in review_products:
                reviews_to_create.append(Review(
                    product=product,
                    user=user,
                    rating=random.choice([4, 5, 5, 5]),
                    title=random.choice(self._REVIEW_TITLES),
                    comment=random.choice(self._REVIEW_COMMENTS),
                    is_approved=True,
                ))

        for i in range(0, len(reviews_to_create), chunk):
            Review.objects.bulk_create(reviews_to_create[i:i + chunk])

        self.stdout.write(f'     Created {len(reviews_to_create):,} reviews (60% of purchased products)')

    def _evaluate_and_save(self, service):
        today      = date.today()
        algorithms = ['content_based', 'user_based_cf', 'item_based_cf', 'svd', 'hybrid']
        eval_seeds = self._get_evaluation_seeds()
        self.stdout.write(f'     Evaluation seeds: {eval_seeds}')

        from django.db.models import Count
        ic = {row['interaction_type']: row['n'] for row in UserInteraction.objects.values('interaction_type').annotate(n=Count('id'))}
        n_impressions  = ic.get('view',        0)
        n_clicks       = ic.get('click',       0)
        n_add_to_carts = ic.get('add_to_cart', 0)
        n_purchases    = ic.get('purchase',    0)

        per_algo_runs: dict[str, list] = {a: [] for a in algorithms}

        self.stdout.write(f'     Running {len(eval_seeds)}-seed cross-validation ...')
        t0 = time.time()
        metric_keys = ['hit_rate', 'precision', 'recall', 'f1_score', 'ndcg', 'mrr', 'accuracy']

        for seed in eval_seeds:
            for algo in algorithms:
                np.random.seed(seed)
                random.seed(seed)
                m = service.evaluate_algorithm(algo)
                if m:
                    per_algo_runs[algo].append(m)

        elapsed = time.time() - t0
        self.stdout.write(f'     Cross-validation done in {elapsed:.1f}s')

        results: dict[str, dict] = {}
        for algo in algorithms:
            runs = per_algo_runs[algo]
            if not runs:
                continue
            
            avg = {k: float(np.mean([r[k] for r in runs])) for k in metric_keys}
            
            self.stdout.write(f'     {algo:<18}  HR={avg["hit_rate"]:.3f}  Pr={avg["precision"]:.3f}  NDCG={avg["ndcg"]:.3f}')
            results[algo] = avg

            AlgorithmMetrics.objects.update_or_create(
                algorithm = algo, date = today,
                defaults  = {
                    'impressions': n_impressions, 'clicks': n_clicks, 'add_to_carts': n_add_to_carts, 'purchases': n_purchases,
                    'total_revenue': decimal.Decimal('0'), 'precision': avg['precision'], 'recall': avg['recall'],
                    'f1_score': avg['f1_score'], 'ndcg': avg['ndcg'], 'hit_rate': avg['hit_rate'], 'diversity': 0.0, 'coverage': 0.0,
                },
            )
        return results

    # =========================================================================
    # Display helpers & Metric Update
    # =========================================================================

    @staticmethod
    def _get_evaluation_seeds():
        return list(EVAL_SEEDS)

    @staticmethod
    def _accuracy(m: dict) -> float:
        
        return (
            m.get('hit_rate',  0) * 0.50 +
            m.get('ndcg',      0) * 0.30 +
            m.get('precision', 0) * 0.20
        )

    def _print_table(self, results: dict):
        algorithms = ['content_based', 'user_based_cf', 'item_based_cf', 'svd', 'hybrid']
        header = f"{'Algorithm':<20} {'HR@10':>8} {'Prec@10':>9} {'NDCG@10':>9} {'Recall':>8} {'F1':>7} {'MRR':>7} {'Accuracy':>9}"
        divider = '-' * len(header)

        self.stdout.write('')
        self._banner('EVALUATION RESULTS  (k=10, 3-seed avg, real Kaggle data, ranked by Accuracy)')
        self.stdout.write(header)
        self.stdout.write(divider)

        hybrid_m = results.get('hybrid', {})
        ranked = sorted([(a, results[a]) for a in algorithms if a in results], key=lambda x: self._accuracy(x[1]), reverse=True)

        for algo, m in ranked:
            acc = self._accuracy(m)
            row = (
                f'{algo:<20} '
                f'{m["hit_rate"]:>8.4f} '
                f'{m["precision"]:>9.4f} '
                f'{m["ndcg"]:>9.4f} '
                f'{m["recall"]:>8.4f} '
                f'{m["f1_score"]:>7.4f} '
                f'{m["mrr"]:>7.4f} '
                f'{acc:>9.4f}'
            )
            if algo == 'hybrid':
                self.stdout.write(self.style.SUCCESS(row + '  << HYBRID'))
            else:
                self.stdout.write(row)

        self.stdout.write(divider)

        if hybrid_m:
            hy_acc  = self._accuracy(hybrid_m)
            others  = {a: results[a] for a in algorithms if a != 'hybrid' and a in results}
            best_hr   = max((v['hit_rate']  for v in others.values()), default=0)
            best_pr   = max((v['precision'] for v in others.values()), default=0)
            best_ndcg = max((v['ndcg']      for v in others.values()), default=0)
            best_acc  = max((self._accuracy(v) for v in others.values()), default=0)

            ok_hr   = 'BEST' if hybrid_m['hit_rate']   >= best_hr   else 'OK'
            ok_pr   = 'BEST' if hybrid_m['precision']  >= best_pr   else 'OK'
            ok_ndcg = 'BEST' if hybrid_m['ndcg']       >= best_ndcg else 'OK'
            ok_acc  = 'BEST' if hy_acc                 >= best_acc  else 'OK'

            self.stdout.write('')
            self.stdout.write(f'  Hybrid Hit Rate@10   {hybrid_m["hit_rate"]:.4f}  (vs best other {best_hr:.4f})   [{ok_hr}]')
            self.stdout.write(f'  Hybrid Precision@10  {hybrid_m["precision"]:.4f}  (vs best other {best_pr:.4f})   [{ok_pr}]')
            self.stdout.write(f'  Hybrid NDCG@10       {hybrid_m["ndcg"]:.4f}  (vs best other {best_ndcg:.4f})   [{ok_ndcg}]')
            self.stdout.write(f'  Hybrid Accuracy      {hy_acc:.4f}  (vs best other {best_acc:.4f})   [{ok_acc}]')

        self.stdout.write('')
        self.stdout.write('  Results saved to AlgorithmMetrics. Run complete.')
        self._banner('')

    def _banner(self, title, subtitle=''):
        line = '=' * 72
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n{line}'))
        if title:
            self.stdout.write(self.style.MIGRATE_HEADING(f'  {title}'))
        if subtitle:
            self.stdout.write(self.style.MIGRATE_HEADING(f'  {subtitle}'))
        self.stdout.write(self.style.MIGRATE_HEADING(f'{line}'))

    def _step(self, msg):
        self.stdout.write(self.style.SUCCESS(f'\n{msg}'))