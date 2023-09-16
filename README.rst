=====
Django Strong Migrations
=====

Django Strong Migrations was inspired by the wonderful [ankane/strong_migrations](https://github.com/ankane/strong_migrations) for rails.


Quick start
-----------

1. Add "strong_migrations" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "polls",
    ]

2. Include the polls URLconf in your project urls.py like this::

    path("polls/", include("polls.urls")),

3. Run ``python manage.py migrate`` to create the polls models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a poll (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/polls/ to participate in the poll.