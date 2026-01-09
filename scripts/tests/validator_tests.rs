use scripts::{QueryValidationError, QueryValidator, ScryfallError};

fn validator() -> QueryValidator {
    QueryValidator::new()
}

// ==================== Valid Query Tests ====================

#[test]
fn test_valid_simple_query() {
    let v = validator();
    assert!(v.validate("type:creature").is_ok());
}

#[test]
fn test_valid_color_query() {
    let v = validator();
    assert!(v.validate("c:red").is_ok());
    assert!(v.validate("color:blue").is_ok());
    assert!(v.validate("id:boros").is_ok());
}

#[test]
fn test_valid_comparison_operators() {
    let v = validator();
    assert!(v.validate("cmc<=3").is_ok());
    assert!(v.validate("cmc>=5").is_ok());
    assert!(v.validate("power>4").is_ok());
    assert!(v.validate("toughness<2").is_ok());
    assert!(v.validate("cmc=3").is_ok());
    assert!(v.validate("cmc!=4").is_ok());
}

#[test]
fn test_valid_complex_query() {
    let v = validator();
    assert!(v.validate("type:creature c:red cmc<=3").is_ok());
    assert!(v.validate("set:neo rarity:rare").is_ok());
}

#[test]
fn test_valid_or_operator() {
    let v = validator();
    assert!(v.validate("type:creature or type:instant").is_ok());
    assert!(v.validate("c:red or c:blue").is_ok());
}

#[test]
fn test_valid_and_operator() {
    let v = validator();
    assert!(v.validate("type:creature and c:green").is_ok());
}

#[test]
fn test_valid_parentheses() {
    let v = validator();
    assert!(v.validate("(type:creature)").is_ok());
    assert!(v.validate("(type:creature or type:instant)").is_ok());
    assert!(v.validate("(c:red or c:blue) type:creature").is_ok());
    assert!(v.validate("((type:creature))").is_ok());
}

#[test]
fn test_valid_quoted_strings() {
    let v = validator();
    assert!(v.validate("name:\"Lightning Bolt\"").is_ok());
    assert!(v.validate("o:\"draw a card\"").is_ok());
    assert!(v.validate("ft:\"flavor text here\"").is_ok());
}

#[test]
fn test_valid_negation() {
    let v = validator();
    assert!(v.validate("-type:creature").is_ok());
    assert!(v.validate("type:creature -c:red").is_ok());
}

#[test]
fn test_valid_special_fields() {
    let v = validator();
    assert!(v.validate("is:commander").is_ok());
    assert!(v.validate("has:watermark").is_ok());
    assert!(v.validate("f:modern").is_ok());
    assert!(v.validate("rarity:mythic").is_ok());
}

// ==================== Empty Query Tests ====================

#[test]
fn test_empty_query() {
    let v = validator();
    assert!(matches!(
        v.validate(""),
        Err(QueryValidationError::EmptyQuery)
    ));
}

#[test]
fn test_whitespace_only_query() {
    let v = validator();
    assert!(matches!(
        v.validate("   "),
        Err(QueryValidationError::EmptyQuery)
    ));
    assert!(matches!(
        v.validate("\t\n"),
        Err(QueryValidationError::EmptyQuery)
    ));
}

// ==================== Unbalanced Parentheses Tests ====================

#[test]
fn test_unbalanced_open_paren() {
    let v = validator();
    assert!(matches!(
        v.validate("(type:creature"),
        Err(QueryValidationError::UnbalancedParentheses)
    ));
}

#[test]
fn test_unbalanced_close_paren() {
    let v = validator();
    assert!(matches!(
        v.validate("type:creature)"),
        Err(QueryValidationError::UnbalancedParentheses)
    ));
}

#[test]
fn test_multiple_unbalanced_parens() {
    let v = validator();
    assert!(matches!(
        v.validate("((type:creature)"),
        Err(QueryValidationError::UnbalancedParentheses)
    ));
    assert!(matches!(
        v.validate("(type:creature))"),
        Err(QueryValidationError::UnbalancedParentheses)
    ));
}

#[test]
fn test_parens_in_quotes_ignored() {
    let v = validator();
    // Parentheses inside quotes should not affect balance
    assert!(v.validate("name:\"(test)\"").is_ok());
    assert!(v.validate("o:\"(draw a card)\"").is_ok());
}

// ==================== Unbalanced Quotes Tests ====================

#[test]
fn test_unbalanced_quotes_single() {
    let v = validator();
    assert!(matches!(
        v.validate("name:\"Lightning Bolt"),
        Err(QueryValidationError::UnbalancedQuotes)
    ));
}

#[test]
fn test_unbalanced_quotes_triple() {
    let v = validator();
    assert!(matches!(
        v.validate("name:\"test\" o:\"another"),
        Err(QueryValidationError::UnbalancedQuotes)
    ));
}

// ==================== Operator Positioning Tests ====================

#[test]
fn test_leading_or_operator() {
    let v = validator();
    assert!(matches!(
        v.validate("or type:creature"),
        Err(QueryValidationError::LeadingOperator)
    ));
}

#[test]
fn test_leading_and_operator() {
    let v = validator();
    assert!(matches!(
        v.validate("and type:creature"),
        Err(QueryValidationError::LeadingOperator)
    ));
}

#[test]
fn test_trailing_or_operator() {
    let v = validator();
    assert!(matches!(
        v.validate("type:creature or"),
        Err(QueryValidationError::TrailingOperator)
    ));
}

#[test]
fn test_trailing_and_operator() {
    let v = validator();
    assert!(matches!(
        v.validate("type:creature and"),
        Err(QueryValidationError::TrailingOperator)
    ));
}

#[test]
fn test_consecutive_operators() {
    let v = validator();
    assert!(matches!(
        v.validate("type:creature and and c:red"),
        Err(QueryValidationError::ConsecutiveOperators)
    ));
    assert!(matches!(
        v.validate("type:creature or or c:blue"),
        Err(QueryValidationError::ConsecutiveOperators)
    ));
    assert!(matches!(
        v.validate("type:creature and or c:green"),
        Err(QueryValidationError::ConsecutiveOperators)
    ));
}

// ==================== URL Encoding Tests ====================

#[test]
fn test_encode_simple_query() {
    let v = validator();
    assert_eq!(v.encode_query("type:creature"), "type%3Acreature");
}

#[test]
fn test_encode_query_with_spaces() {
    let v = validator();
    let encoded = v.encode_query("type:creature c:red");
    assert!(encoded.contains("%20") || encoded.contains("+"));
}

#[test]
fn test_encode_query_with_quotes() {
    let v = validator();
    let encoded = v.encode_query("name:\"Lightning Bolt\"");
    assert!(encoded.contains("%22"));
}

// ==================== Edge Cases ====================

#[test]
fn test_valid_single_word() {
    let v = validator();
    // A single word without operators should be valid (searches card names)
    assert!(v.validate("lightning").is_ok());
}

#[test]
fn test_case_insensitive_operators() {
    let v = validator();
    // Operators should be case-insensitive
    assert!(v.validate("type:creature OR type:instant").is_ok());
    assert!(v.validate("type:creature AND c:red").is_ok());
}

#[test]
fn test_mixed_valid_query() {
    let v = validator();
    assert!(v
        .validate("(type:creature or type:instant) c:red cmc<=3 -is:reprint")
        .is_ok());
}

#[test]
fn test_default_trait() {
    let v = QueryValidator::default();
    assert!(v.validate("type:creature").is_ok());
}

// ==================== Error Display Tests ====================

#[test]
fn test_error_display() {
    assert_eq!(
        format!("{}", QueryValidationError::EmptyQuery),
        "Query cannot be empty"
    );
    assert_eq!(
        format!("{}", QueryValidationError::UnbalancedParentheses),
        "Unbalanced parentheses in query"
    );
    assert_eq!(
        format!("{}", QueryValidationError::UnbalancedQuotes),
        "Unbalanced quotes in query"
    );
    assert_eq!(
        format!("{}", QueryValidationError::LeadingOperator),
        "Query cannot start with an operator"
    );
    assert_eq!(
        format!("{}", QueryValidationError::TrailingOperator),
        "Query cannot end with an operator"
    );
    assert_eq!(
        format!("{}", QueryValidationError::ConsecutiveOperators),
        "Consecutive operators are not allowed"
    );
}

#[test]
fn test_scryfall_error_display() {
    let validation_err = ScryfallError::ValidationError(QueryValidationError::EmptyQuery);
    assert!(format!("{}", validation_err).contains("Query validation failed"));
}
