# -*- coding: utf-8 -*-

from __future__ import absolute_import
import falcon
import logging
from snakebite.controllers.hooks import deserialize, serialize
from snakebite.controllers.schema.restaurant import RestaurantSchema
from snakebite.models.restaurant import Restaurant, Menu
from snakebite.libs.error import HTTPBadRequest
from snakebite.helpers.geolocation import reformat_geolocations_map_to_list, reformat_geolocations_point_field_to_map
from snakebite.helpers.range import min_max
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned, ValidationError


# -------- BEFORE_HOOK functions
def deserialize_create(req, res, resource):
    deserialize(req, res, resource, schema=RestaurantSchema())
    req.params['body'] = reformat_geolocations_map_to_list(req.params['body'], ['geolocation'])


def deserialize_update(req, res, id, resource):
    deserialize(req, res, resource, schema=RestaurantSchema())
    req.params['body'] = reformat_geolocations_map_to_list(req.params['body'], ['geolocation'])

# -------- END functions

logger = logging.getLogger(__name__)


class Collection(object):
    def __init__(self):
        pass

    @falcon.before(deserialize)
    @falcon.after(serialize)
    def on_get(self, req, res):
        query_params = req.params.get('query')

        try:
            # get pagination limits
            start = int(query_params.pop('start', 0))
            limit = int(query_params.pop('limit', 20))
            end = start + limit

        except ValueError as e:
            raise HTTPBadRequest(title='Invalid Value',
                                 description='Invalid arguments in URL query:\n{}'.format(e.message))

        # custom filters
        # temp dict for updating query filters
        updated_params = {}

        for item in ['name', 'description', 'menus.name']:
            if item in query_params:
                item_val = query_params.pop(item)
                updated_params['{}__icontains'.format(item)] = item_val

        # skip updating query_params for filters on list fields like tags or menus.tags,
        # since mongoengine filters directly by finding any Restaurant that has tags of that value
        # e.g., GET /restaurants?tags=chicken returns all restaurants having 'chicken' tag

        try:
            if 'geolocation' in query_params:
                geolocation_val = query_params.pop('geolocation')
                geolocation_val = map(float, geolocation_val.split(',')[:2])
                max_distance = int(query_params.pop('maxDistance', 1000))  # defaulted to 1km

                # we deal with geolocation query in raw instead due to mongoengine bugs
                # see https://github.com/MongoEngine/mongoengine/issues/795
                # dated: 3/1/2015

                updated_params['__raw__'] = {
                    'geolocation': {
                        '$near': {
                            '$geometry': {
                                'type': 'Point',
                                'coordinates': geolocation_val
                            },
                            '$maxDistance': max_distance
                        },
                    }
                }

        except Exception:
            raise HTTPBadRequest('Invalid Value', 'geolocation supplied is invalid: {}'.format(geolocation_val))

        if 'price' in query_params:
            price_range = query_params.pop('price')
            price_min, price_max = min_max(price_range, type='float')
            updated_params['menus.price__gte'] = price_min
            updated_params['menus.price__lte'] = price_max

        query_params.update(updated_params)  # update modified params for filtering

        restaurants = Restaurant.objects(**query_params)[start:end]
        for r in restaurants:
            reformat_geolocations_point_field_to_map(r, 'geolocation')

        res.body = {'items': restaurants, 'count': len(restaurants)}

    @falcon.before(deserialize_create)
    @falcon.after(serialize)
    def on_post(self, req, res):
        data = req.params.get('body')

        # save to DB
        menu_data = data.pop('menus')  # extract info meant for menus

        restaurant = Restaurant(**data)
        restaurant.menus = [Menu(**menu) for menu in menu_data]

        restaurant.save()

        restaurant = Restaurant.objects.get(id=restaurant.id)

        res.body = restaurant
        res.body = reformat_geolocations_point_field_to_map(res.body, 'geolocation')


class Item(object):
    def __init__(self):
        pass

    def _try_get_restaurant(self, id):
        try:
            return Restaurant.objects.get(id=id)
        except (ValidationError, DoesNotExist, MultipleObjectsReturned) as e:
            raise HTTPBadRequest(title='Invalid Value', description='Invalid ID provided. {}'.format(e.message))

    @falcon.after(serialize)
    def on_get(self, req, res, id):
        restaurant = self._try_get_restaurant(id)
        res.body = reformat_geolocations_point_field_to_map(restaurant, 'geolocation')


    @falcon.after(serialize)
    def on_delete(self, req, res, id):
        restaurant = self._try_get_restaurant(id)
        restaurant.delete()

    # TODO: handle PUT requests
    @falcon.before(deserialize_update)
    @falcon.after(serialize)
    def on_put(self, req, res, id):
        restaurant = self._try_get_restaurant(id)
        data = req.params.get('body')

        # save to DB
        menu_data = data.pop('menus')  # extract info meant for menus
        for key, value in data.iteritems():
            setattr(restaurant, key, value)

        restaurant.menus = [Menu(**menu) for menu in menu_data]

        restaurant.save()

        restaurant = Restaurant.objects.get(id=id)
        res.body = restaurant
        res.body = reformat_geolocations_point_field_to_map(res.body, 'geolocation')
