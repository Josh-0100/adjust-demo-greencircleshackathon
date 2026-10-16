'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { api, errorMessage } from '@/lib/api';
export function useApi<T>(path: string, role?: 'resident' | 'staff' | 'admin') {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const latest = useRef(0);
  const reload = useCallback(async () => {
    const request = ++latest.current;
    setLoading(true); setError(null);
    try { const response = await api<T>(path, { role }); if (request === latest.current) setData(response); } catch (e) { if (request === latest.current) setError(errorMessage(e)); } finally { if (request === latest.current) setLoading(false); }
  }, [path, role]);
  useEffect(() => { void reload(); return () => { latest.current += 1; }; }, [reload]);
  return { data, loading, error, reload, setData };
}
