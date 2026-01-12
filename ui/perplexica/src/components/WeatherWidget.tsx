import { Cloud, Sun, CloudRain, CloudSnow, Wind } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

const WeatherWidget = () => {
  const [data, setData] = useState({
    temperature: 0,
    condition: '',
    location: '',
    humidity: 0,
    windSpeed: 0,
    icon: '',
    temperatureUnit: 'C',
    windSpeedUnit: 'm/s',
  });

  const [loading, setLoading] = useState(true);

  const locationRef = useRef<{
    latitude: number;
    longitude: number;
    city: string;
  } | null>(null);

  const getApproxLocation = useCallback(async () => {
    const res = await fetch('https://ipwhois.app/json/');
    const data = await res.json();

    return {
      latitude: data.latitude,
      longitude: data.longitude,
      city: data.city,
    };
  }, []);

  const getLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      return getApproxLocation();
    }

    const getCurrentPosition = () =>
      new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });

    const getReverseGeocode = async (latitude: number, longitude: number) => {
      const res = await fetch(
        `https://api-bdc.io/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        },
      );

      const data = await res.json();

      return {
        latitude,
        longitude,
        city: data.locality,
      };
    };

    try {
      if (navigator.permissions?.query) {
        const result = await navigator.permissions.query({
          name: 'geolocation',
        });

        if (result.state === 'granted') {
          const position = await getCurrentPosition();
          return getReverseGeocode(
            position.coords.latitude,
            position.coords.longitude,
          );
        }
        if (result.state === 'prompt') {
          const approx = await getApproxLocation();
          navigator.geolocation.getCurrentPosition(() => {});
          return approx;
        }
        if (result.state === 'denied') {
          return getApproxLocation();
        }
      }

      const position = await getCurrentPosition();
      return getReverseGeocode(
        position.coords.latitude,
        position.coords.longitude,
      );
    } catch (error) {
      console.error('Failed to resolve location, using approx location.', error);
      return getApproxLocation();
    }
  }, [getApproxLocation]);

  const updateWeather = useCallback(async () => {
    const location = locationRef.current ?? (await getLocation());

    if (!locationRef.current) {
      locationRef.current = location;
    }

    const res = await fetch(`/api/weather`, {
      method: 'POST',
      body: JSON.stringify({
        lat: location.latitude,
        lng: location.longitude,
        measureUnit: localStorage.getItem('measureUnit') ?? 'Metric',
      }),
    });

    const data = await res.json();

    if (res.status !== 200) {
      console.error('Error fetching weather data');
      setLoading(false);
      return;
    }

    setData({
      temperature: data.temperature,
      condition: data.condition,
      location: location.city,
      humidity: data.humidity,
      windSpeed: data.windSpeed,
      icon: data.icon,
      temperatureUnit: data.temperatureUnit,
      windSpeedUnit: data.windSpeedUnit,
    });
    setLoading(false);
  }, [getLocation]);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const scheduleNextUpdate = async () => {
      if (timeoutId) {
        return;
      }
      await updateWeather();
      if (cancelled) {
        return;
      }
      timeoutId = setTimeout(() => {
        timeoutId = null;
        scheduleNextUpdate();
      }, 60 * 1000);
    };

    const clearScheduledUpdate = () => {
      if (!timeoutId) {
        return;
      }
      clearTimeout(timeoutId);
      timeoutId = null;
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        scheduleNextUpdate();
      } else {
        clearScheduledUpdate();
      }
    };

    handleVisibilityChange();
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      cancelled = true;
      clearScheduledUpdate();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [updateWeather]);

  return (
    <div className="bg-light-secondary dark:bg-dark-secondary rounded-2xl border border-light-200 dark:border-dark-200 shadow-sm shadow-light-200/10 dark:shadow-black/25 flex flex-row items-center w-full h-24 min-h-[96px] max-h-[96px] px-3 py-2 gap-3">
      {loading ? (
        <>
          <div className="flex flex-col items-center justify-center w-16 min-w-16 max-w-16 h-full animate-pulse">
            <div className="h-10 w-10 rounded-full bg-light-200 dark:bg-dark-200 mb-2" />
            <div className="h-4 w-10 rounded bg-light-200 dark:bg-dark-200" />
          </div>
          <div className="flex flex-col justify-between flex-1 h-full py-1 animate-pulse">
            <div className="flex flex-row items-center justify-between">
              <div className="h-3 w-20 rounded bg-light-200 dark:bg-dark-200" />
              <div className="h-3 w-12 rounded bg-light-200 dark:bg-dark-200" />
            </div>
            <div className="h-3 w-16 rounded bg-light-200 dark:bg-dark-200 mt-1" />
            <div className="flex flex-row justify-between w-full mt-auto pt-1 border-t border-light-200 dark:border-dark-200">
              <div className="h-3 w-16 rounded bg-light-200 dark:bg-dark-200" />
              <div className="h-3 w-8 rounded bg-light-200 dark:bg-dark-200" />
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="flex flex-col items-center justify-center w-16 min-w-16 max-w-16 h-full">
            <img
              src={`/weather-ico/${data.icon}.svg`}
              alt={data.condition}
              className="h-10 w-auto"
            />
            <span className="text-base font-semibold text-black dark:text-white">
              {data.temperature}°{data.temperatureUnit}
            </span>
          </div>
          <div className="flex flex-col justify-between flex-1 h-full py-2">
            <div className="flex flex-row items-center justify-between">
              <span className="text-sm font-semibold text-black dark:text-white">
                {data.location}
              </span>
              <span className="flex items-center text-xs text-black/60 dark:text-white/60 font-medium">
                <Wind className="w-3 h-3 mr-1" />
                {data.windSpeed} {data.windSpeedUnit}
              </span>
            </div>
            <span className="text-xs text-black/50 dark:text-white/50 italic">
              {data.condition}
            </span>
            <div className="flex flex-row justify-between w-full mt-auto pt-2 border-t border-light-200/50 dark:border-dark-200/50 text-xs text-black/50 dark:text-white/50 font-medium">
              <span>Humidity {data.humidity}%</span>
              <span className="font-semibold text-black/70 dark:text-white/70">
                Now
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default WeatherWidget;
