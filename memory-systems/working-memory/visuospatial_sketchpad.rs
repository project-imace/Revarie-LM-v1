//! visuospatial_sketchpad.rs
//! Working Memory – Visuospatial Sketchpad.
//! Implements Baddeley's visuospatial sketchpad component of working memory.
//! Temporarily stores visual and spatial information (objects, colors, locations).
//! Based on Baddeley & Hitch (1974) and Logie (1995).

use std::collections::VecDeque;
use std::time::{Duration, Instant};

/// A visual object stored in the sketchpad.
#[derive(Debug, Clone, PartialEq)]
pub struct VisualObject {
    /// Object identifier.
    pub id: String,
    /// Visual features (color, shape, size).
    pub features: VisualFeatures,
    /// Spatial location (x, y coordinates normalized 0-1).
    pub location: (f64, f64),
    /// Timestamp for decay tracking.
    pub timestamp: Instant,
}

/// Visual features of an object.
#[derive(Debug, Clone, PartialEq)]
pub struct VisualFeatures {
    pub color: Option<String>,
    pub shape: Option<String>,
    pub size: f64,  // relative size 0-1
    pub orientation: f64,  // degrees 0-360
}

impl Default for VisualFeatures {
    fn default() -> Self {
        Self {
            color: None,
            shape: None,
            size: 0.1,
            orientation: 0.0,
        }
    }
}

impl VisualObject {
    pub fn new(id: impl Into<String>, location: (f64, f64)) -> Self {
        Self {
            id: id.into(),
            features: VisualFeatures::default(),
            location,
            timestamp: Instant::now(),
        }
    }

    pub fn with_color(mut self, color: impl Into<String>) -> Self {
        self.features.color = Some(color.into());
        self
    }

    pub fn with_shape(mut self, shape: impl Into<String>) -> Self {
        self.features.shape = Some(shape.into());
        self
    }

    pub fn with_size(mut self, size: f64) -> Self {
        self.features.size = size.clamp(0.0, 1.0);
        self
    }
}

/// Visuospatial Sketchpad – maintains visual and spatial information.
pub struct VisuospatialSketchpad {
    /// Visual cache (objects and features).
    visual_cache: VecDeque<VisualObject>,
    /// Spatial locations (can be independent of objects).
    spatial_locations: VecDeque<(f64, f64)>,
    /// Maximum number of objects (~4 according to Luck & Vogel, 1997).
    object_capacity: usize,
    /// Decay duration for unattended items (~2-3 seconds).
    decay_duration: Duration,
    /// Whether active rehearsal (visual imagery) is enabled.
    imagery_active: bool,
}

impl Default for VisuospatialSketchpad {
    fn default() -> Self {
        Self {
            visual_cache: VecDeque::new(),
            spatial_locations: VecDeque::new(),
            object_capacity: 4,
            decay_duration: Duration::from_secs(2),
            imagery_active: true,
        }
    }
}

impl VisuospatialSketchpad {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_capacity(mut self, capacity: usize) -> Self {
        self.object_capacity = capacity;
        self
    }

    pub fn with_decay(mut self, duration: Duration) -> Self {
        self.decay_duration = duration;
        self
    }

    /// Insert a visual object.
    pub fn insert_object(&mut self, object: VisualObject) -> bool {
        self.cleanup();
        if self.visual_cache.len() >= self.object_capacity {
            self.visual_cache.pop_front();
        }
        self.visual_cache.push_back(object);
        true
    }

    /// Insert a spatial location.
    pub fn insert_location(&mut self, location: (f64, f64)) {
        if self.spatial_locations.len() >= self.object_capacity {
            self.spatial_locations.pop_front();
        }
        self.spatial_locations.push_back(location);
    }

    /// Remove decayed items.
    pub fn cleanup(&mut self) -> usize {
        let now = Instant::now();
        let before = self.visual_cache.len();
        self.visual_cache.retain(|obj| {
            now.duration_since(obj.timestamp) < self.decay_duration
        });
        before - self.visual_cache.len()
    }

    /// Perform visual imagery rehearsal (refreshes timestamps).
    pub fn rehearse(&mut self) {
        if !self.imagery_active {
            return;
        }
        let now = Instant::now();
        for obj in self.visual_cache.iter_mut() {
            obj.timestamp = now;
        }
    }

    /// Recall all currently active visual objects.
    pub fn recall_objects(&mut self) -> Vec<VisualObject> {
        self.cleanup();
        self.visual_cache.iter().cloned().collect()
    }

    /// Recall objects with rehearsal.
    pub fn recall_with_imagery(&mut self) -> Vec<VisualObject> {
        self.rehearse();
        self.recall_objects()
    }

    /// Recall spatial locations.
    pub fn recall_locations(&self) -> Vec<(f64, f64)> {
        self.spatial_locations.iter().cloned().collect()
    }

    /// Find object nearest to a location.
    pub fn nearest_to(&self, location: (f64, f64)) -> Option<VisualObject> {
        self.visual_cache
            .iter()
            .min_by(|a, b| {
                let dist_a = (a.location.0 - location.0).powi(2) + (a.location.1 - location.1).powi(2);
                let dist_b = (b.location.0 - location.0).powi(2) + (b.location.1 - location.1).powi(2);
                dist_a.partial_cmp(&dist_b).unwrap()
            })
            .cloned()
    }

    pub fn len(&self) -> usize {
        self.visual_cache.len()
    }

    pub fn is_empty(&self) -> bool {
        self.visual_cache.is_empty()
    }

    pub fn clear(&mut self) {
        self.visual_cache.clear();
        self.spatial_locations.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread::sleep;

    #[test]
    fn test_insert_and_recall() {
        let mut vss = VisuospatialSketchpad::new();
        let obj = VisualObject::new("obj1", (0.5, 0.5))
            .with_color("red")
            .with_shape("circle");
        vss.insert_object(obj);
        let recalled = vss.recall_objects();
        assert_eq!(recalled.len(), 1);
        assert_eq!(recalled[0].id, "obj1");
        assert_eq!(recalled[0].features.color, Some("red".to_string()));
    }

    #[test]
    fn test_capacity_limit() {
        let mut vss = VisuospatialSketchpad::new().with_capacity(2);
        vss.insert_object(VisualObject::new("A", (0.0, 0.0)));
        vss.insert_object(VisualObject::new("B", (0.0, 0.0)));
        vss.insert_object(VisualObject::new("C", (0.0, 0.0)));
        let recalled = vss.recall_objects();
        assert_eq!(recalled.len(), 2);
        assert!(recalled.iter().any(|o| o.id == "B"));
        assert!(recalled.iter().any(|o| o.id == "C"));
    }

    #[test]
    fn test_spatial_locations() {
        let mut vss = VisuospatialSketchpad::new();
        vss.insert_location((0.2, 0.8));
        vss.insert_location((0.9, 0.1));
        let locations = vss.recall_locations();
        assert_eq!(locations, vec![(0.2, 0.8), (0.9, 0.1)]);
    }

    #[test]
    fn test_nearest_object() {
        let mut vss = VisuospatialSketchpad::new();
        vss.insert_object(VisualObject::new("A", (0.0, 0.0)));
        vss.insert_object(VisualObject::new("B", (1.0, 1.0)));
        let nearest = vss.nearest_to((0.2, 0.2)).unwrap();
        assert_eq!(nearest.id, "A");
    }

    #[test]
    fn test_decay() {
        let mut vss = VisuospatialSketchpad::new()
            .with_decay(Duration::from_millis(10));
        vss.insert_object(VisualObject::new("decay", (0.0, 0.0)));
        sleep(Duration::from_millis(20));
        let recalled = vss.recall_objects();
        assert!(recalled.is_empty());
    }

    #[test]
    fn test_imagery_rehearsal() {
        let mut vss = VisuospatialSketchpad::new()
            .with_decay(Duration::from_millis(50));
        vss.insert_object(VisualObject::new("keep", (0.0, 0.0)));
        sleep(Duration::from_millis(30));
        vss.rehearse();
        sleep(Duration::from_millis(30));
        let recalled = vss.recall_objects();
        assert_eq!(recalled.len(), 1);
    }
}
