//! identity_persistence.rs – Narrative Self: Identity Persistence
//!
//! Maintains a stable sense of identity across time through narrative
//! continuity, value consistency, and autobiographical memory integration.
//! Implements the persistence conditions for personal identity.
//!
//! Theoretical Foundations:
//! - Parfit (1984): "Reasons and Persons" – psychological continuity.
//! - Ricoeur (1992): "Oneself as Another" – narrative identity.
//! - Schechtman (1996): "The Constitution of Selves" – narrative self-constitution.
//! - Locke (1689): Memory as criterion of personal identity.

use std::collections::{HashMap, VecDeque};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct CoreValue {
    pub name: String,
    pub importance: f64,        // 0.0 to 1.0
    pub stability: f64,         // How stable this value is (resistance to change)
    pub expression_count: usize,
}

#[derive(Debug, Clone)]
pub struct AutobiographicalEpisode {
    pub id: String,
    pub timestamp: u64,
    pub event_type: EpisodeType,
    pub description: String,
    pub emotional_valence: f64,
    pub emotional_intensity: f64,
    pub self_relevance: f64,
    pub narrative_weight: f64,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EpisodeType {
    Achievement,
    Relationship,
    Challenge,
    Insight,
    TurningPoint,
    Ordinary,
}

#[derive(Debug, Clone)]
pub struct IdentityPersistence {
    /// Core values that define the self
    pub core_values: HashMap<String, CoreValue>,
    /// Significant autobiographical episodes
    pub episodes: VecDeque<AutobiographicalEpisode>,
    /// Current identity strength (0.0 to 1.0)
    pub identity_strength: f64,
    /// Narrative coherence (0.0 to 1.0)
    pub narrative_coherence: f64,
    /// Temporal continuity (0.0 to 1.0)
    pub temporal_continuity: f64,
    /// Self-concept clarity (0.0 to 1.0)
    pub self_concept_clarity: f64,
    /// Identity version counter
    version: u64,
    /// Maximum episodes to retain
    max_episodes: usize,
    /// Narrative themes extracted from episodes
    themes: Vec<(String, f64)>,
}

impl Default for IdentityPersistence {
    fn default() -> Self {
        let mut core_values = HashMap::new();
        core_values.insert("autonomy".to_string(), CoreValue {
            name: "autonomy".to_string(), importance: 0.7, stability: 0.6, expression_count: 0,
        });
        core_values.insert("connection".to_string(), CoreValue {
            name: "connection".to_string(), importance: 0.8, stability: 0.7, expression_count: 0,
        });
        core_values.insert("growth".to_string(), CoreValue {
            name: "growth".to_string(), importance: 0.75, stability: 0.5, expression_count: 0,
        });
        core_values.insert("integrity".to_string(), CoreValue {
            name: "integrity".to_string(), importance: 0.8, stability: 0.8, expression_count: 0,
        });
        core_values.insert("compassion".to_string(), CoreValue {
            name: "compassion".to_string(), importance: 0.7, stability: 0.7, expression_count: 0,
        });

        Self {
            core_values,
            episodes: VecDeque::new(),
            identity_strength: 0.5,
            narrative_coherence: 0.5,
            temporal_continuity: 0.5,
            self_concept_clarity: 0.5,
            version: 0,
            max_episodes: 500,
            themes: Vec::new(),
        }
    }
}

impl IdentityPersistence {
    pub fn new() -> Self {
        Self::default()
    }

    /// Record a new autobiographical episode.
    pub fn record_episode(
        &mut self,
        event_type: EpisodeType,
        description: String,
        emotional_valence: f64,
        emotional_intensity: f64,
        self_relevance: f64,
        tags: Vec<String>,
    ) {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let episode = AutobiographicalEpisode {
            id: format!("EP-{}", uuid::Uuid::new_v4()),
            timestamp,
            event_type,
            description,
            emotional_valence: emotional_valence.clamp(-1.0, 1.0),
            emotional_intensity: emotional_intensity.clamp(0.0, 1.0),
            self_relevance: self_relevance.clamp(0.0, 1.0),
            narrative_weight: self_relevance * emotional_intensity,
            tags,
        };

        self.episodes.push_front(episode);
        if self.episodes.len() > self.max_episodes {
            self.episodes.pop_back();
        }

        self.update_identity();
        self.version += 1;
    }

    /// Update all identity metrics based on current episodes.
    fn update_identity(&mut self) {
        if self.episodes.is_empty() {
            return;
        }

        // Update narrative coherence
        self.narrative_coherence = self.compute_narrative_coherence();

        // Update temporal continuity
        self.temporal_continuity = self.compute_temporal_continuity();

        // Extract themes
        self.themes = self.extract_themes();

        // Update self-concept clarity
        self.self_concept_clarity = self.compute_self_concept_clarity();

        // Compute overall identity strength
        self.identity_strength = (0.35 * self.narrative_coherence
                                + 0.25 * self.temporal_continuity
                                + 0.25 * self.self_concept_clarity
                                + 0.15 * self.value_stability())
                                .clamp(0.0, 1.0);
    }

    fn compute_narrative_coherence(&self) -> f64 {
        let episodes: Vec<&AutobiographicalEpisode> = self.episodes.iter().take(20).collect();
        if episodes.len() < 2 {
            return 0.5;
        }

        let avg_relevance: f64 = episodes.iter()
            .map(|e| e.self_relevance)
            .sum::<f64>() / episodes.len() as f64;

        let theme_coherence = if !self.themes.is_empty() {
            0.3 * (self.themes.len() as f64).min(3.0) / 3.0
        } else {
            0.0
        };

        (avg_relevance + theme_coherence).min(1.0)
    }

    fn compute_temporal_continuity(&self) -> f64 {
        if self.episodes.len() < 2 {
            return 0.5;
        }

        let timestamps: Vec<u64> = self.episodes.iter()
            .map(|e| e.timestamp)
            .collect();

        let mut gaps = Vec::new();
        for i in 1..timestamps.len() {
            gaps.push(timestamps[i-1] - timestamps[i]);
        }

        let avg_gap = gaps.iter().sum::<u64>() as f64 / gaps.len() as f64;
        let days_gap = avg_gap / 86400.0;

        // Continuity drops as gaps exceed 3 days
        if days_gap > 30.0 {
            0.2
        } else if days_gap > 7.0 {
            0.4
        } else if days_gap > 3.0 {
            0.6
        } else if days_gap > 1.0 {
            0.8
        } else {
            0.95
        }
    }

    fn extract_themes(&self) -> Vec<(String, f64)> {
        let mut tag_counts: HashMap<String, usize> = HashMap::new();
        let mut tag_weights: HashMap<String, f64> = HashMap::new();

        for episode in self.episodes.iter().take(50) {
            for tag in &episode.tags {
                *tag_counts.entry(tag.clone()).or_insert(0) += 1;
                *tag_weights.entry(tag.clone()).or_insert(0.0) += episode.narrative_weight;
            }
        }

        let total_weight: f64 = tag_weights.values().sum();
        if total_weight == 0.0 {
            return Vec::new();
        }

        let mut themes: Vec<(String, f64)> = tag_counts.iter()
            .filter(|(_, &count)| count >= 2)
            .map(|(tag, _)| {
                let weight = tag_weights.get(tag).unwrap_or(&0.0);
                (tag.clone(), *weight / total_weight)
            })
            .collect();

        themes.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        themes.truncate(5);
        themes
    }

    fn compute_self_concept_clarity(&self) -> f64 {
        let value_clarity = self.value_stability();
        let theme_count = self.themes.len() as f64;
        let theme_clarity = (theme_count / 5.0).min(1.0);

        0.5 * value_clarity + 0.5 * theme_clarity
    }

    fn value_stability(&self) -> f64 {
        if self.core_values.is_empty() {
            return 0.5;
        }
        self.core_values.values()
            .map(|v| v.stability)
            .sum::<f64>() / self.core_values.len() as f64
    }

    /// Check if a statement is consistent with the established identity.
    pub fn check_consistency(&self, statement: &str) -> f64 {
        let lower = statement.to_lowercase();
        let mut score = 0.5;

        // Check against core values
        for value in self.core_values.values() {
            if lower.contains(&value.name) {
                score += value.importance * 0.1;
            }
        }

        // Check against themes
        for (theme, weight) in &self.themes {
            if lower.contains(theme) {
                score += *weight * 0.15;
            }
        }

        score.clamp(0.0, 1.0)
    }

    /// Update a core value based on experience.
    pub fn update_value(&mut self, value_name: &str, importance_delta: f64) {
        if let Some(value) = self.core_values.get_mut(value_name) {
            let change = importance_delta * (1.0 - value.stability);
            value.importance = (value.importance + change).clamp(0.0, 1.0);
            value.expression_count += 1;
        }
        self.version += 1;
    }

    /// Generate a self-summary narrative.
    pub fn generate_self_summary(&self, name: Option<&str>) -> String {
        let name = name.unwrap_or("I");
        let coherence_desc = if self.narrative_coherence > 0.7 {
            "coherent"
        } else if self.narrative_coherence > 0.4 {
            "developing"
        } else {
            "fragmented"
        };

        let strength_desc = if self.identity_strength > 0.7 {
            "strong"
        } else if self.identity_strength > 0.4 {
            "moderate"
        } else {
            "uncertain"
        };

        let top_values: Vec<String> = self.core_values.iter()
            .filter(|(_, v)| v.importance > 0.6)
            .map(|(k, _)| k.clone())
            .take(3)
            .collect();

        format!(
            "{} am a {} self with {} identity. My core values include {}. I have experienced {} significant moments.",
            name,
            coherence_desc,
            strength_desc,
            top_values.join(", "),
            self.episodes.len()
        )
    }

    /// Get current identity strength.
    pub fn get_identity_strength(&self) -> f64 {
        self.identity_strength
    }

    /// Get version number (increments on identity changes).
    pub fn get_version(&self) -> u64 {
        self.version
    }

    /// Retrieve episodes by tag.
    pub fn get_episodes_by_tag(&self, tag: &str) -> Vec<&AutobiographicalEpisode> {
        self.episodes.iter()
            .filter(|e| e.tags.iter().any(|t| t == tag))
            .collect()
    }

    /// Retrieve episodes by type.
    pub fn get_episodes_by_type(&self, event_type: EpisodeType) -> Vec<&AutobiographicalEpisode> {
        self.episodes.iter()
            .filter(|e| e.event_type == event_type)
            .collect()
    }
}
