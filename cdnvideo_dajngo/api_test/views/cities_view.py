from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import City
from ..serializers import CitySerializer
import os
from dotenv import load_dotenv
import requests
import math

load_dotenv()


def load_coord(city):
    key = os.getenv('KEY_LOAD')
    res = requests.get(
        f'https://catalog.api.2gis.com/3.0/items/geocode?q={city}&type=adm_div.city&fields=items.point&key={key}')
    return res.json()['result']['items'][0]['point']['lat'], res.json()['result']['items'][0]['point']['lon'], \
        res.json()['result']['items'][0]['full_name']


def math_distance(cities, lat, lon):
    l = []
    for i in cities:
        R = 6371.0

        lat1 = math.radians(lat)
        lon1 = math.radians(lon)
        lat2 = math.radians(i.latitude)
        lon2 = math.radians(i.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        l.append({'name': i.name, 'latitude': i.latitude, 'longitude': i.longitude, 'distance': distance})
        print(distance)
    l.sort(key=lambda x: x['distance'])
    return l[:2]


class CityMain(APIView):
    def get(self, request):
        if request.query_params.get('name'):
            queryset = City.objects.filter(name=request.query_params.get('name').capitalize()).first()
            serializer = CitySerializer(queryset)
            return Response(serializer.data)
        elif request.query_params.get('latitude') and request.query_params.get('longitude'):
            lat = float(request.query_params.get('latitude'))
            lon = float(request.query_params.get('longitude'))
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                return Response({'detail': 'Incorrect latitude and longitude input'}, status=status.HTTP_400_BAD_REQUEST)
            cities = City.objects.all()
            result = math_distance(cities, lat, lon)
            return Response(result)
        cities = City.objects.all()
        serializer = CitySerializer(cities, many=True)
        return Response(serializer.data)

    def post(self, request):
        name = request.data.get('name').capitalize()
        if name:
            city = City.objects.filter(name=name).first()
            try:
                lat, lon, name = load_coord(name)
            except Exception as e:
                return Response({'detail': 'City not found'}, status=status.HTTP_400_BAD_REQUEST)
            data = {'name': name,
                    'latitude': lat,
                    'longitude': lon
                    }
            if city:
                serializer = CitySerializer(city, data=data)
            else:
                serializer = CitySerializer(data=data)
        else:
            return Response({'detail': 'Name field is required'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK if city else status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        name = request.query_params.get('name')
        if name:
            city = City.objects.filter(name=name).first()
            if city:
                city.delete()
                return Response({'detail': 'City deleted successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'City not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Name field is required'}, status=status.HTTP_400_BAD_REQUEST)
