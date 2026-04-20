//! test_turing_tape.rs
//! Unit tests for the Turing Tape implementation.

#[cfg(test)]
mod tests {
    use crate::turing_tape::{TapeCell, TuringTape};

    #[test]
    fn test_sparse_tape_memory_efficiency() {
        let mut tape = TuringTape::new();
        // Write far apart to test sparse representation
        tape.write(TapeCell::Symbol('X'));
        for _ in 0..1000 {
            tape.move_right();
        }
        tape.write(TapeCell::Symbol('Y'));
        // The tape should not allocate memory for the 1000 blank cells.
        assert_eq!(tape.read(), TapeCell::Symbol('Y'));
        for _ in 0..1000 {
            tape.move_left();
        }
        assert_eq!(tape.read(), TapeCell::Symbol('X'));
    }

    #[test]
    fn test_tape_unbounded_left() {
        let mut tape = TuringTape::new();
        tape.write(TapeCell::Symbol('A'));
        for _ in 0..100 {
            tape.move_left();
        }
        assert_eq!(tape.read(), TapeCell::Blank);
        tape.write(TapeCell::Symbol('Z'));
        assert_eq!(tape.read(), TapeCell::Symbol('Z'));
    }
}
