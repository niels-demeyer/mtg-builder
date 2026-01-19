// Scryfall API card type
export interface ScryfallCard {
  id: string;
  name: string;
  mana_cost?: string;
  cmc: number;
  type_line: string;
  oracle_text?: string;
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
