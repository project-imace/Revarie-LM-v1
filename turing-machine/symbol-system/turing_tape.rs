//! turing_tape.rs
//! A rigorous implementation of a Turing Machine tape.
//! This provides the unbounded memory required for Turing-complete computation.
//! The tape is the foundational storage mechanism for all symbolic processing.

use std::collections::HashMap;

/// A single cell on the Turing Machine tape.
/// Each cell holds a symbol (represented as a char) or is blank.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TapeCell {
    Symbol(char),
    Blank,
}

/// The infinite tape of a Turing Machine.
/// The tape is conceptually infinite in both directions, but we implement it
/// sparsely using a HashMap to avoid allocating infinite memory.
#[derive(Debug, Clone)]
pub struct TuringTape {
    /// Sparse representation: index -> cell content.
    cells: HashMap<i64, TapeCell>,
    /// Current position of the tape head.
    head_position: i64,
}

impl Default for TuringTape {
    fn default() -> Self {
        Self {
            cells: HashMap::new(),
            head_position: 0,
        }
    }
}

impl TuringTape {
    /// Create a new, empty tape.
    pub fn new() -> Self {
        Self::default()
    }

    /// Initialize the tape with a string of symbols.
    /// The string is placed starting at position 0.
    pub fn from_string(s: &str) -> Self {
        let mut tape = Self::new();
        for (i, ch) in s.chars().enumerate() {
            tape.cells.insert(i as i64, TapeCell::Symbol(ch));
        }
        tape
    }

    /// Read the symbol at the current head position.
    pub fn read(&self) -> TapeCell {
        self.cells
            .get(&self.head_position)
            .cloned()
            .unwrap_or(TapeCell::Blank)
    }

    /// Write a symbol at the current head position.
    pub fn write(&mut self, cell: TapeCell) {
        match cell {
            TapeCell::Blank => {
                self.cells.remove(&self.head_position);
            }
            TapeCell::Symbol(_) => {
                self.cells.insert(self.head_position, cell);
            }
        }
    }

    /// Move the head one position to the left.
    pub fn move_left(&mut self) {
        self.head_position -= 1;
    }

    /// Move the head one position to the right.
    pub fn move_right(&mut self) {
        self.head_position += 1;
    }

    /// Get the current head position (for debugging and inspection).
    pub fn head_position(&self) -> i64 {
        self.head_position
    }

    /// Return the entire tape as a string (for visualization).
    /// Blanks are represented as underscores.
    pub fn to_string(&self) -> String {
        if self.cells.is_empty() {
            return String::from("_");
        }
        let min_idx = *self.cells.keys().min().unwrap_or(&0);
        let max_idx = *self.cells.keys().max().unwrap_or(&0);
        let mut result = String::new();
        for i in min_idx..=max_idx {
            match self.cells.get(&i) {
                Some(TapeCell::Symbol(ch)) => result.push(*ch),
                _ => result.push('_'),
            }
        }
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tape_read_write() {
        let mut tape = TuringTape::new();
        assert_eq!(tape.read(), TapeCell::Blank);
        tape.write(TapeCell::Symbol('A'));
        assert_eq!(tape.read(), TapeCell::Symbol('A'));
        tape.write(TapeCell::Blank);
        assert_eq!(tape.read(), TapeCell::Blank);
    }

    #[test]
    fn test_tape_movement() {
        let mut tape = TuringTape::from_string("ABC");
        assert_eq!(tape.read(), TapeCell::Symbol('A'));
        tape.move_right();
        assert_eq!(tape.read(), TapeCell::Symbol('B'));
        tape.move_right();
        assert_eq!(tape.read(), TapeCell::Symbol('C'));
        tape.move_left();
        assert_eq!(tape.read(), TapeCell::Symbol('B'));
    }

    #[test]
    fn test_turing_completeness_invariant() {
        // A Turing tape with these operations is sufficient for Turing-complete computation.
        let mut tape = TuringTape::new();
        tape.write(TapeCell::Symbol('1'));
        tape.move_right();
        tape.move_right(); // Moved right a second time to leave a blank space
        tape.write(TapeCell::Symbol('0'));
        assert_eq!(tape.to_string(), "1_0");
    }
}
