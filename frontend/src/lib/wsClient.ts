/**
 * WebSocket client for multiplayer game communication.
 *
 * Manages connection to ws://localhost:8000/api/v1/ws/game?token=<jwt>
 * Provides typed send/receive with automatic reconnection.
 */

const WS_BASE = "ws://localhost:8000/api/v1";

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

export interface ServerMessage {
  type: string;
  [key: string]: any;
}

export interface ClientMessage {
  type: string;
  [key: string]: any;
}

export interface WSClientOptions {
  onMessage: (message: ServerMessage) => void;
  onStatusChange: (status: ConnectionStatus) => void;
  onError: (error: string) => void;
}

export class GameWSClient {
  private ws: WebSocket | null = null;
  private options: WSClientOptions;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private token: string | null = null;

  constructor(options: WSClientOptions) {
    this.options = options;
  }

  connect(token: string): void {
    this.disconnect();
    this.token = token;
    this.options.onStatusChange("connecting");

    this.ws = new WebSocket(`${WS_BASE}/ws/game?token=${token}`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.options.onStatusChange("connected");
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as ServerMessage;
        this.options.onMessage(message);
      } catch {
        this.options.onError("Failed to parse server message");
      }
    };

    this.ws.onclose = (event: CloseEvent) => {
      if (
        !event.wasClean &&
        this.token &&
        this.reconnectAttempts < this.maxReconnectAttempts
      ) {
        this.scheduleReconnect();
      } else {
        this.options.onStatusChange("disconnected");
      }
    };

    this.ws.onerror = () => {
      this.options.onError("WebSocket connection error");
      this.options.onStatusChange("error");
    };
  }

  send(message: ClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    this.token = null;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.onclose = null; // prevent reconnect on intentional disconnect
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }
    this.reconnectAttempts = 0;
    this.options.onStatusChange("disconnected");
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      30000
    );
    this.options.onStatusChange("connecting");
    this.reconnectTimeout = setTimeout(() => {
      if (this.token) {
        this.connect(this.token);
      }
    }, delay);
  }
}
