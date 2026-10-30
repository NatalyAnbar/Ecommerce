# E-Commerce REST API

[![Tests](https://github.com/NatalyAnbar/Ecommerce/actions/workflows/tests.yml/badge.svg)](https://github.com/NatalyAnbar/Ecommerce/actions/workflows/tests.yml)
![Tests count](https://img.shields.io/badge/tests-150%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/Django-6.1-092E20)
![DRF](https://img.shields.io/badge/DRF-3.18-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

A complete backend for an online store, built with Django REST Framework.

It covers the whole shopping journey: signing up, browsing a bilingual catalog (English and Arabic), filling a cart as a guest, merging that cart after login, and checking out into an order that updates stock safely, even when many customers buy the same product at the same moment.

The project is tested with **150 automated tests**, runs on **PostgreSQL in Docker**, and every push is checked by **GitHub Actions**.

## Table of Contents

- [Highlights](#highlights)
- [Features](#features)
  - [Accounts and Authentication](#accounts-and-authentication)
  - [Catalog](#catalog)
  - [Product Images](#product-images)
  - [Reviews](#reviews)
  - [Cart](#cart)
  - [Orders and Stock](#orders-and-stock)
  - [Roles and Permissions](#roles-and-permissions)
  - [Security and Rate Limiting](#security-and-rate-limiting)
- [Design Decisions](#design-decisions)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Endpoints](#endpoints)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)

<a id="highlights"></a>

## Highlights

- **Safe concurrent checkout:** row-level locks (`select_for_update`) and `F()` expressions inside one transaction, so stock can never go below zero or be sold twice
- **Guest carts that survive login:** shop without an account, then merge the guest cart into your own after logging in
- **Bilingual catalog:** names and descriptions in English and Arabic, chosen by the `Accept-Language` header
- **JWT with rotation and logout:** refresh tokens are rotated and blacklisted, and logout revokes them
- **Strict image validation:** format, file size, dimensions, aspect ratio and a per-product limit
- **Price snapshots:** each order stores the price paid, so later price changes never rewrite history
- **150 tests** running on PostgreSQL in CI

<a id="features"></a>

## Features

<a id="accounts-and-authentication"></a>

### Accounts and Authentication

- Custom user model that logs in with **email** instead of a username
- **Registration** with password confirmation and Django's password rules (minimum length, common passwords, numeric-only, similarity to the user's details)
- Emails are **case-insensitive**: `Nataly@mail.com` and `nataly@mail.com` can't be two accounts
- **JWT authentication** with access and refresh tokens
- **Refresh token rotation:** every refresh returns a new refresh token and blacklists the old one, so a stolen token stops working after one use
- **Logout** that blacklists the refresh token
- **Profile** endpoint (`/me/`) with no id in the URL: the user always comes from the token, so nobody can read another user's profile
- **Change password** with the old password required, and the new one checked against the same rules

<a id="catalog"></a>

### Catalog

- Categories and products with **English and Arabic** names and descriptions
- The response language follows the `Accept-Language` header (`en` or `ar`), with English as the fallback
- **Slugs** generated automatically from the English name, unique even when two products share a name (`iphone`, `iphone-1`, ...)
- **Filtering** by category, brand and price range: `?category=phones&price_min=100&price_max=500`
- **Search** across both languages and the brand: `?search=apple`
- **Ordering** by price: `?ordering=-price`
- **Pagination** with a client-chosen page size, capped at 30: `?page_size=5`
- **Average rating and review count** on every product, calculated in the database with `annotate()` so they are never out of date
- Queries optimized with `select_related` and `prefetch_related` to avoid N+1 problems, with tests that check the number of queries

<a id="product-images"></a>

### Product Images

- Upload **several images at once** while creating or updating a product
- The product and its images are saved in **one transaction**: if one image is invalid, nothing is saved
- The first uploaded image becomes the **main image** automatically if the product has none
- Validation on every image:

| Rule | Limit |
|---|---|
| Formats | JPG, JPEG, PNG, WEBP (SVG is blocked because it can contain scripts) |
| File size | 5 MB at most |
| Dimensions | from 500×500 up to 5000×5000 pixels |
| Aspect ratio | no wider or taller than 2:1 |
| Images per product | 8 at most |

- Images have their own endpoint for listing, editing titles, replacing the file and deleting

<a id="reviews"></a>

### Reviews

- 1 to 5 star ratings with an optional comment
- **One review per user per product**, enforced in both the serializer (clear 400 error) and the database (unique constraint)
- Only the author can edit or delete their review
- If a user deletes their account, their reviews stay, so the product's rating history is kept

<a id="cart"></a>

### Cart

- Works **without an account**: a guest cart is identified by a **UUID**, so its id can't be guessed
- Logged-in users have **one cart each**
- Adding a product that's already in the cart **increases its quantity** instead of adding a second line
- Quantity per product is **between 1 and 100**, including when adding to an existing line
- A cart line can't be switched to another product; quantities are changed with `PATCH`
- **Clear** the whole cart in one request
- **Merge after login:** the guest cart is moved into the user's cart inside a transaction; products in both carts are added up (capped at 100) and the guest cart is deleted
- Totals are always calculated from **current prices**
- A logged-in user can only reach their own cart; a guest can only reach guest carts

<a id="orders-and-stock"></a>

### Orders and Stock

- **Checkout** turns the cart into an order:
  - Empty cart → `400`
  - Not enough stock → `400` with the names of the products that are short
  - Otherwise the order is created, stock is reduced, and the cart is emptied
- Everything happens in **one database transaction**: if any step fails, nothing changes
- Products are **locked** while checking stock (`select_for_update`), so two customers can't buy the last item at the same time
- Stock is reduced with **`F()` expressions** in the database, avoiding lost updates
- Each order item keeps a **snapshot of the unit price** at the moment of purchase
- Products that appear in orders **can't be deleted** (`PROTECT`), so order history stays complete
- Order status: `pending`, `paid` or `cancelled`
- **Cancel** a pending order, which returns its items to stock in one transaction; other statuses return `400`
- Users can only list, view and cancel **their own orders**
- Admin panel with order items shown inline and read-only, filters by status and date, and search by email

<a id="roles-and-permissions"></a>

### Roles and Permissions

- Anyone can browse the catalog; changes require Django model permissions
- A **Product Managers** group created by a management command (`setup_roles`) can manage products, categories and images, but can't delete categories
- The command is safe to run many times and warns about missing permissions

<a id="security-and-rate-limiting"></a>

### Security and Rate Limiting

- **Login is limited to 5 attempts per minute** to slow down password guessing
- Global limits: 100 requests per hour for guests (by IP), 1000 per hour for logged-in users
- Secrets and database settings come from environment variables (`.env`), never from the code
- `DEBUG` is off unless the environment turns it on
- Admin flags like `is_staff` can't be set through registration

<a id="design-decisions"></a>

## Design Decisions

A few choices that are worth explaining:

| Decision | Why |
|---|---|
| UUID for cart ids | Guest carts have no owner, so the id is the only key. A UUID can't be guessed like `1, 2, 3`. |
| `unit_price` on order items | Prices change. An order must show what the customer actually paid. |
| `select_for_update` + `F()` in checkout | Without locks, two checkouts can read the same stock and both succeed, selling more than exists. |
| `PROTECT` on order items' product | Deleting a product must not delete the orders that contain it. |
| Rating calculated with `annotate()` | A stored average can go out of date; calculating it in the query keeps it correct. |
| One review per product in two places | The serializer gives a friendly error; the database constraint is the final guarantee. |
| No id in `/me/` | The user comes from the token, which removes a whole class of access bugs. |
| `PATCH` only for cart items and images | `PUT` would require resending the product or the image file just to change one field. |

<a id="tech-stack"></a>

## Tech Stack

| Area | Tools |
|---|---|
| Language | Python 3.13 |
| Framework | Django 6.1, Django REST Framework 3.18 |
| Authentication | djangorestframework-simplejwt (rotation and blacklist) |
| Database | PostgreSQL 16 |
| Filtering | django-filter |
| Nested URLs | drf-nested-routers |
| Images | Pillow |
| API docs | drf-spectacular (Swagger UI and ReDoc) |
| Testing | pytest, pytest-django, model-bakery |
| DevOps | Docker, Docker Compose, GitHub Actions |
| Configuration | django-environ |

<a id="getting-started"></a>

## Getting Started

### Option 1: Docker (recommended)

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/NatalyAnbar/Ecommerce.git
cd Ecommerce/Ecommerce
cp .env.example .env          # then fill in your own values
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py setup_roles
docker compose exec web python manage.py createsuperuser
```

The API is now running at http://127.0.0.1:8000.

### Option 2: Local virtual environment

Requires Python 3.13. PostgreSQL still runs in Docker.

```bash
git clone https://github.com/NatalyAnbar/Ecommerce.git
cd Ecommerce/Ecommerce
cp .env.example .env          # use 127.0.0.1 as the host in DATABASE_URL
python -m venv venv
venv\Scripts\activate         # on macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
python manage.py migrate
python manage.py setup_roles
python manage.py runserver
```

### Environment variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hosts, e.g. `localhost,127.0.0.1` |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Used by the PostgreSQL container |
| `DATABASE_URL` | e.g. `postgres://user:password@127.0.0.1:5432/dbname` |

<a id="api-documentation"></a>

## API Documentation

Once the server is running:

- **Swagger UI:** http://127.0.0.1:8000/api/docs/
- **ReDoc:** http://127.0.0.1:8000/api/redoc/
- **OpenAPI schema:** http://127.0.0.1:8000/api/schema/

To try protected endpoints, log in, copy the `access` token, click **Authorize** in Swagger and paste it.

<a id="endpoints"></a>

## Endpoints

### Accounts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/accounts/register/` | Sign up |
| `POST` | `/accounts/login/` | Get access and refresh tokens (5 attempts per minute) |
| `POST` | `/accounts/refreshtoken/` | Get a new access token and a rotated refresh token |
| `POST` | `/accounts/logout/` | Blacklist the refresh token |
| `GET` `PATCH` | `/accounts/me/` | Read or update my profile |
| `PUT` | `/accounts/change_password/` | Change my password |

### Catalog

| Method | Endpoint | Description |
|---|---|---|
| `GET` `POST` | `/store/categories/` | List or create categories |
| `GET` `PUT` `PATCH` `DELETE` | `/store/categories/{slug}/` | One category with its products |
| `GET` `POST` | `/store/products/` | List (filter, search, order, paginate) or create products with images |
| `GET` `PUT` `PATCH` `DELETE` | `/store/products/{slug}/` | One product |
| `GET` | `/store/products/{slug}/images/` | A product's images |
| `GET` `PATCH` `DELETE` | `/store/products/{slug}/images/{id}/` | Edit or delete one image |
| `GET` `POST` | `/store/products/{slug}/reviews/` | List or write reviews |
| `GET` `PUT` `PATCH` `DELETE` | `/store/products/{slug}/reviews/{id}/` | One review (author only for changes) |

### Cart

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/cart/carts/` | Create a cart (guest or logged in) |
| `GET` | `/cart/carts/{id}/` | View a cart with its total |
| `DELETE` | `/cart/carts/{id}/clear/` | Remove every item |
| `GET` `POST` | `/cart/carts/{cart_id}/cartitems/` | List or add items |
| `PATCH` `DELETE` | `/cart/carts/{cart_id}/cartitems/{id}/` | Change a quantity or remove an item |
| `POST` | `/cart/mergeCart/` | Merge a guest cart into my cart after login |

### Orders

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/orders/checkout/` | Create an order from my cart |
| `GET` | `/orders/` | List my orders |
| `GET` | `/orders/{id}/` | One order with its items and total |
| `POST` | `/orders/{id}/cancel/` | Cancel a pending order and restore stock |

<a id="running-tests"></a>

## Running Tests

```bash
docker compose up -d db
pytest
```

**150 tests** across every part of the project:

| Area | What is tested |
|---|---|
| Accounts | registration rules, profile, change password, JWT login, refresh rotation, blacklist, logout, login throttling |
| Catalog | categories, products, slugs, filtering, search, ordering, pagination, Arabic and English responses, query counts, roles |
| Images | formats, size, dimensions, aspect ratio, per-product limit, main image |
| Reviews | one per user, owner-only changes |
| Cart | guest and user carts, adding and merging quantities, the 100 limit, access to other carts, clear, merge |
| Orders | checkout, empty cart, not enough stock, price snapshot, stock reduction, cancel and restore, access to other users' orders |

Tests run automatically on every push and pull request with GitHub Actions, against a real PostgreSQL service. The workflow also fails if a model change is missing its migration.

<a id="project-structure"></a>

## Project Structure

```
Ecommerce/
├── accounts/        # custom user, registration, JWT login, refresh, logout, profile
├── store/           # categories, products, images, reviews, filters, pagination, roles command
├── cart/            # guest and user carts, cart items, merge
├── order/           # orders, checkout, cancellation, stock
├── Ecommerce/       # settings, URLs, language middleware
├── conftest.py      # shared test fixtures
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Author

**Nataly Anbar** · [GitHub](https://github.com/NatalyAnbar)
