import type { CardFace } from './types';

/** Check if a card has two renderable faces (both with separate images). */
export function isDFC(card: { card_faces?: CardFace[] }): boolean {
  if (!card.card_faces || card.card_faces.length < 2) return false;
  return !!card.card_faces[0]?.image_uris && !!card.card_faces[1]?.image_uris;
}

/** Get the image URL for a specific face of a card. */
export function getFaceImage(
  card: { card_faces?: CardFace[]; image_uri?: string; image_uris?: { small: string; normal: string; large: string } },
  faceIndex: number,
  size: 'small' | 'normal' | 'large' = 'normal'
): string {
  if (card.card_faces && card.card_faces.length > faceIndex) {
    const face = card.card_faces[faceIndex];
    if (face?.image_uris) {
      return face.image_uris[size] || face.image_uris.normal || '';
    }
  }
  // Fallback to top-level image
  if (card.image_uris) return card.image_uris[size] || card.image_uris.normal || '';
  return (card as { image_uri?: string }).image_uri || '';
}

/** Get metadata (name, type, oracle text, etc.) for a specific face. */
export function getFaceData(
  card: { card_faces?: CardFace[]; name: string; type_line?: string; oracle_text?: string; mana_cost?: string; power?: string; toughness?: string },
  faceIndex: number
): { name: string; type_line: string; oracle_text?: string; mana_cost?: string; power?: string; toughness?: string } {
  if (card.card_faces && card.card_faces.length > faceIndex) {
    const face = card.card_faces[faceIndex];
    return {
      name: face.name || card.name,
      type_line: face.type_line || card.type_line || '',
      oracle_text: face.oracle_text,
      mana_cost: face.mana_cost,
      power: face.power,
      toughness: face.toughness,
    };
  }
  return {
    name: card.name,
    type_line: card.type_line || '',
    oracle_text: card.oracle_text,
    mana_cost: card.mana_cost,
    power: card.power,
    toughness: card.toughness,
  };
}
