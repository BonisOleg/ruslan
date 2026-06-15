#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

mkdir -p media/products media/categories media/blog

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_pages || true
PRODUCT_COUNT=$(python manage.py shell -c "from apps.catalog.models import Product; print(Product.objects.count())")
if [ "$PRODUCT_COUNT" = "0" ]; then
    echo "No products found — running initial import..."
    python manage.py import_csv || true
else
    echo "Products already exist ($PRODUCT_COUNT) — skipping import."
fi
python manage.py import_csv --resync-wholesale || true
