import { useState, useEffect } from 'react';
import wsService from '../services/websocket';

export const useAlerts = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      wsService.connect(token);
      const unsubscribe = wsService.subscribe((alert) => {
        setAlerts(prev => [alert, ...prev].slice(0, 50));
      });
      return () => {
        unsubscribe();
        wsService.disconnect();
      };
    }
  }, []);

  return alerts;
};
