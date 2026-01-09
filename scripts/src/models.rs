use serde::Deserialize;

#[allow(dead_code)]
#[derive(Deserialize, Debug)]
pub struct ScryfallSearchResponse {
    pub object: String,
    pub total_cards: u32,
    pub has_more: bool,
    pub next_page: Option<String>,
    pub data: Vec<Card>,
}

#[allow(dead_code)]
#[derive(Deserialize, Debug, Clone)]
pub struct Card {
    pub id: String,
    pub name: String,
    pub mana_cost: Option<String>,
    pub type_line: Option<String>,
    pub oracle_text: Option<String>,
    pub set_name: String,
    pub rarity: String,
}
