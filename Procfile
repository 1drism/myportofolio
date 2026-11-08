release: python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py seed_cv --sync
web: gunicorn portofolio.wsgi
