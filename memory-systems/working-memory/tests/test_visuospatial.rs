//! test_visuospatial.rs
//! Unit tests for Visuospatial Sketchpad.

#[cfg(test)]
mod tests {
    use std::thread::sleep;
    use std::time::Duration;

    include!("../visuospatial_sketchpad.rs");

    #[test]
    fn test_insert_and_recall_object() {
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

    #[test]
    fn test_clear() {
        let mut vss = VisuospatialSketchpad::new();
        vss.insert_object(VisualObject::new("obj", (0.0, 0.0)));
        vss.insert_location((0.5, 0.5));
        assert!(!vss.is_empty());
        vss.clear();
        assert!(vss.is_empty());
        assert_eq!(vss.recall_locations().len(), 0);
    }
}
