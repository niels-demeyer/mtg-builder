// Scryfall API card type
export interface ScryfallCard {
  id: string;
  name: string;
  mana_cost?: string;
  cmc: number;
  type_line: string;
  oracle_text?: string;
  flavor_text?: string;
  power?: string;
  toughness?: string;
  colors?: string[];
  color_identity: string[];
  rarity: string;
  set: string;
  set_name: string;
  image_uris?: {
    small: string;
    normal: string;
    large: string;
    png: string;
    art_crop: string;
    border_crop: string;
  };
  card_faces?: Array<{
    name: string;
    mana_cost?: string;
    type_line: string;
    oracle_text?: string;
    image_uris?: {
      small: string;
      normal: string;
      large: string;
      png: string;
      art_crop: string;
      border_crop: string;
    };
  }>;
  prices: {
    usd?: string;
    usd_foil?: string;
    eur?: string;
  };
  legalities: Record<string, string>;
}

export interface DbCard {
  id: string;
  name: string;
  mana_cost?: string;
  cmc: number;
  power?: string;
  toughness?: string;
  type_line: string;
  oracle_text?: string;
  colors?: string[];
  color_identity: string[];
  rarity: string;
  keywords?: string[];
  set: string;
  set_name: string;
  image_uris?: {
    small: string;
    normal: string;
    large: string;
    png: string;
    art_crop: string;
    border_crop: string;
  };
  legalities: Record<string, string>;
}

// Card zones for deck organization
export type CardZone =
  | "mainboard"
  | "sideboard"
  | "maybeboard"
  | "considering"
  | "commander";

// Display modes for card visualization
export type DisplayMode = "list" | "grid" | "pile";

// Sort options for pile view
export type PileSortBy = "cmc" | "type" | "color" | "rarity";

// Predefined card tags
export type CardTag =
  | "Ramp"
  | "Removal"
  | "Win Con"
  | "Draw"
  | "Protection"
  | "Tutor"
  | "Board Wipe"
  | "Counter"
  | "Recursion"
  | "Custom";

// Card in a deck with quantity and additional metadata
export interface CardInDeck {
  id: string;
  name: string;
  mana_cost?: string;
  cmc: number;
  type_line: string;
  oracle_text?: string;
  flavor_text?: string;
  power?: string;
  toughness?: string;
  colors?: string[];
  rarity: string;
  image_uri?: string;
  quantity: number;
  zone: CardZone;
  tags: string[];
  isCommander?: boolean;
}

// Folder for organizing decks
export interface DeckFolder {
  id: string;
  name: string;
  color?: string;
  parentId?: string;
  order: number;
}

// Deck type with enhanced features
export interface Deck {
  id: string;
  name: string;
  format: DeckFormat;
  description: string;
  cards: CardInDeck[];
  folderId?: string;
  thumbnail?: string;
  createdAt: string;
  updatedAt: string;
}

// Supported deck formats
export type DeckFormat =
  | "Standard"
  | "Modern"
  | "Legacy"
  | "Vintage"
  | "Commander"
  | "Pioneer"
  | "Pauper"
  | "Historic"
  | "Brawl"
  | "Custom";

// Deck statistics
export interface DeckStats {
  totalCards: number;
  mainboardCount: number;
  sideboardCount: number;
  maybeboardCount: number;
  consideringCount: number;
  manaCurve: Record<number, number>;
  colorDistribution: Record<string, number>;
  typeDistribution: Record<string, number>;
  averageCmc: number;
  landCount: number;
  creatureCount: number;
  spellCount: number;
}

// App settings for user preferences
export interface AppSettings {
  defaultDisplayMode: DisplayMode;
  defaultPileSort: PileSortBy;
  showCardPrices: boolean;
  autoSave: boolean;
}

// Deck store state
export interface DeckStoreState {
  decks: Deck[];
  folders: DeckFolder[];
  currentDeck: Deck | null;
  displayMode: DisplayMode;
  pileSortBy: PileSortBy;
  selectedZone: CardZone;
  loading: boolean;
  error: string | null;
}

// Deck updates (partial)
export interface DeckUpdates {
  name?: string;
  format?: DeckFormat;
  description?: string;
  cards?: CardInDeck[];
  folderId?: string;
  thumbnail?: string;
}

// Drag item type for drag and drop
export interface DragItem {
  cardId: string;
  sourceZone: CardZone;
  index: number;
}

// ============================================
// Game Types for Opening Hands / Gameplay
// ============================================

// Game zones where cards can exist during gameplay
export type GameZone =
  | "library"
  | "hand"
  | "battlefield"
  | "graveyard"
  | "exile"
  | "command";

// A card instance in the game (unique per card, even if same card name)
export interface GameCard {
  instanceId: string;       // Unique ID for this instance
  cardId: string;           // Original card ID from deck
  name: string;
  mana_cost?: string;
  cmc: number;
  type_line: string;
  oracle_text?: string;
  power?: string;
  toughness?: string;
  colors?: string[];
  rarity: string;
  image_uri?: string;
  zone: GameZone;
  isTapped: boolean;
  counters: Record<string, number>;
  attachedTo?: string;      // instanceId of card this is attached to
  faceDown: boolean;
  isCommander?: boolean;
}

// Mana pool tracking
export interface ManaPool {
  W: number;  // White
  U: number;  // Blue
  B: number;  // Black
  R: number;  // Red
  G: number;  // Green
  C: number;  // Colorless
}

// Player state in a game
export interface PlayerState {
  id: string;
  name: string;
  life: number;
  poison: number;
  commanderDamage: Record<string, number>; // Commander ID -> damage taken
  manaPool: ManaPool;
  library: GameCard[];
  hand: GameCard[];
  battlefield: GameCard[];
  graveyard: GameCard[];
  exile: GameCard[];
  command: GameCard[];      // Command zone for commanders
}

// Game state for managing a game session
export interface GameState {
  id: string;
  deckId: string;
  deckName: string;
  format: DeckFormat;
  player: PlayerState;
  turnNumber: number;
  phase: GamePhase;
  history: GameAction[];
  mulliganCount: number;
  started: boolean;
}

// Game phases
export type GamePhase =
  | "untap"
  | "upkeep"
  | "draw"
  | "main1"
  | "combat_begin"
  | "combat_attackers"
  | "combat_blockers"
  | "combat_damage"
  | "combat_end"
  | "main2"
  | "end"
  | "cleanup";

// Actions that can be recorded in game history
export interface GameAction {
  id: string;
  timestamp: number;
  type: GameActionType;
  cardInstanceId?: string;
  fromZone?: GameZone;
  toZone?: GameZone;
  details?: string;
}

export type GameActionType =
  | "draw"
  | "play"
  | "discard"
  | "tap"
  | "untap"
  | "exile"
  | "destroy"
  | "return"
  | "shuffle"
  | "mulligan"
  | "scry"
  | "mill"
  | "life_change"
  | "counter_add"
  | "counter_remove";

// Opening hand evaluation result
export interface OpeningHandEvaluation {
  keepScore: number;        // 0-100 score
  landCount: number;
  nonLandCount: number;
  averageCmc: number;
  hasEarlyPlay: boolean;    // Has 1-2 cmc playable
  hasMidGame: boolean;      // Has 3-4 cmc playable
  colorCoverage: string[];  // Colors represented in hand
  suggestions: string[];    // AI suggestions
}

// Game store state
export interface GameStoreState {
  game: GameState | null;
  selectedCard: GameCard | null;
  isLoading: boolean;
  error: string | null;
}

// ============================================
// Multiplayer Game Types
// ============================================

export interface MultiplayerGameState {
  id: string;
  game_code: string;
  format: DeckFormat;
  players: PlayerState[];
  active_player_id: string;
  turn_number: number;
  phase: GamePhase;
  turn_order: string[];
  started: boolean;
  history: GameAction[];
}

export interface LobbyPlayer {
  id: string;
  username: string;
  deck_name: string;
  ready: boolean;
}

// Redacted player state for opponents (hidden zones replaced with counts)
export interface OpponentPlayerState extends Omit<PlayerState, 'library' | 'hand'> {
  library_count: number;
  hand_count: number;
  library: GameCard[];   // empty array for opponents
  hand: GameCard[];      // empty array for opponents
}

// Action interface for GameBoard dual-mode support
export interface GameBoardActions {
  drawCard: () => void;
  moveCard: (instanceId: string, toZone: GameZone) => void;
  playCard: (instanceId: string) => void;
  playCardWithMana: (instanceId: string, genericAllocation?: Partial<ManaPool>) => { success: boolean; error?: string };
  toggleTap: (instanceId: string) => void;
  tapLandForMana: (instanceId: string, color: string) => void;
  untapAll: () => void;
  nextTurn: () => void;
  setPhase: (phase: GamePhase) => void;
  updateLife: (change: number) => void;
  addCounter: (instanceId: string, counterType: string) => void;
  removeCounter: (instanceId: string, counterType: string) => void;
  shuffleLibrary: () => void;
  mill: (count: number) => void;
  discardCard: (instanceId: string) => void;
  addMana: (color: string, amount?: number) => void;
  removeMana: (color: string, amount?: number) => void;
  clearManaPool: () => void;
  selectCard: (card: GameCard | null) => void;
}

// Effective game info for GameBoard (abstracted from single/multiplayer)
export interface GameBoardInfo {
  turnNumber: number;
  phase: GamePhase;
  deckName: string;
  format: string;
  started: boolean;
}

// Multiplayer store state
export interface MultiplayerStoreState {
  connectionStatus: "disconnected" | "connecting" | "connected" | "error";
  gameCode: string | null;
  lobbyPlayers: LobbyPlayer[];
  isHost: boolean;
  game: MultiplayerGameState | null;
  myPlayerId: string | null;
  selectedCard: GameCard | null;
  error: string | null;
  actionError: string | null;
}

// WebSocket message types
export type ClientMessageType =
  | "create_game"
  | "join_game"
  | "leave_game"
  | "game_action";

export type ServerMessageType =
  | "game_created"
  | "player_joined"
  | "player_left"
  | "game_started"
  | "game_state_update"
  | "action_rejected"
  | "game_over"
  | "error"
  | "left_game";
