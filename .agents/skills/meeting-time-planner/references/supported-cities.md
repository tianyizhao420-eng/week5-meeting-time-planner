# Supported Cities

The script recognises the following city names (case-insensitive).
You may also pass any valid IANA timezone string (e.g. `America/Chicago`) in place of a city name.

## North America
New York / NYC, Boston, Washington DC, Miami, Atlanta, Chicago, Houston, Dallas,
Denver, Phoenix, Los Angeles / LA, San Francisco / SF, Seattle,
Toronto, Montreal, Vancouver, Mexico City, São Paulo, Buenos Aires,
Santiago, Bogota

## Europe
London, Dublin, Lisbon, Madrid, Paris, Amsterdam, Brussels, Berlin, Frankfurt,
Munich, Zurich, Geneva, Rome, Milan, Vienna, Prague, Warsaw, Stockholm, Oslo,
Copenhagen, Helsinki, Athens, Istanbul, Moscow, Kyiv

## Middle East & Africa
Dubai, Abu Dhabi, Riyadh, Tel Aviv, Jerusalem, Cairo, Nairobi, Johannesburg,
Cape Town, Lagos, Accra

## South & Southeast Asia
Mumbai, Delhi / New Delhi, Bangalore, Hyderabad, Kolkata, Karachi, Lahore,
Dhaka, Colombo, Kathmandu, Bangkok, Ho Chi Minh, Hanoi, Jakarta,
Kuala Lumpur, Singapore, Manila

## East Asia
Beijing, Shanghai, Guangzhou, Shenzhen, Hong Kong / HK, Taipei, Seoul, Tokyo, Osaka

## Oceania
Sydney, Melbourne, Brisbane, Perth, Auckland, Wellington, Honolulu

---

If your city is not listed, find its IANA timezone at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones and pass it directly with `--source` or in the `--cities` argument.
