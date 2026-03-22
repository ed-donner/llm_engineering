from requests.exceptions import ChunkedEncodingError
from http.client import IncompleteRead
from googlemaps.maps import StaticMapMarker

import googlemaps
import time

def get_center(points):
    if not points:
        raise ValueError("points must be a non-empty list of coordinate objects")

    locations = []
    lats, lngs = [], []
    for p in points:
        g = p.get("geoCode")
        lat = p.get("latitude", g.get("latitude"))
        lng = p.get("longitude", g.get("longitude"))
        if lat is None or lng is None:
            raise ValueError("Each point must include 'latitude' and 'longitude' (or 'geoCode.latitude'/'geoCode.longitude').")
        lat_f = float(lat)
        lng_f = float(lng)
        locations.append({"lat": lat_f, "lng": lng_f})
        lats.append(lat_f)
        lngs.append(lng_f)

    # Center at the centroid of provided points
    center = (sum(lats) / len(lats), sum(lngs) / len(lngs))
    return center, locations


class MapGenerator:
    def __init__(self, google_map_api_key):
        self.client = googlemaps.Client(google_map_api_key)

    def fetch_static_map_bytes(
            self,
            center,
            markers,
            size=(400, 400),
            zoom=6,
            map_type="hybrid",
            img_format="png",
            scale=2,
            visible=None,
            max_retries=3,
            backoff_base=0.6,
    ):
        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                iterator = self.client.static_map(
                    size=size,
                    zoom=zoom,
                    center=center,
                    maptype=map_type,
                    format=img_format,
                    scale=scale,
                    visible=visible,
                    markers=markers,
                )
                return b"".join(chunk for chunk in iterator if chunk)
            except (ChunkedEncodingError, IncompleteRead) as e:
                last_err = e
                if attempt == max_retries:
                    break
                # An exponential backoff before retrying
                time.sleep(backoff_base * attempt)
        # If we got here, all retries failed; re-raise the last error, so the user sees the cause.
        raise last_err

    def generate(
            self,
            points,
            zoom=6,
            size=(600, 600),
            map_type="roadmap",
            color="blue",
            label=None,
            marker_size="mid"
    ):
        center, locations = get_center(points)

        sm_marker = StaticMapMarker(
            locations=locations,
            size=marker_size,
            color=color,
            label=label,
        )

        img_bytes = self.fetch_static_map_bytes(
            center=center,
            markers=[sm_marker],
            size=size,
            zoom=zoom,
            map_type=map_type,
            img_format="png",
            scale=2,
        )

        return img_bytes