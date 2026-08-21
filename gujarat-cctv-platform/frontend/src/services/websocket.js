class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.listeners = new Set();
  }

  connect(token) {
    this.ws = new WebSocket(`ws://${window.location.host}/ws/alerts?token=${token}`);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.listeners.forEach(listener => listener(data));
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < 5) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect(token);
        }, 2000 * this.reconnectAttempts);
      }
    };
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default new WebSocketService();
