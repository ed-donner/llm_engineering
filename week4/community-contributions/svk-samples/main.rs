use std::time::Instant;

const N: usize = 10000;
const INITIAL_SEED: u32 = 42;
const MIN_VAL: i32 = -10;
const MAX_VAL: i32 = 10;

struct Lcg {
    state: u32,
}
impl Lcg {
    fn new(seed: u32) -> Self {
        Lcg { state: seed }
    }
}
impl Iterator for Lcg {
    type Item = u32;
    fn next(&mut self) -> Option<Self::Item> {
        const A: u32 = 1664525;
        const C: u32 = 1013904223;
        let next = self.state.wrapping_mul(A).wrapping_add(C);
        self.state = next;
        Some(next)
    }
}

fn max_subarray_sum_fast(n: usize, seed: u32, min_val: i32, max_val: i32) -> i64 {
    let range = (max_val - min_val + 1) as u32;
    let mut lcg = Lcg::new(seed);
    let mut max_sum = i64::MIN;
    let mut cur_sum = 0i64;
    for _ in 0..n {
        let r = lcg.next().unwrap() % range;
        let v = r as i32 + min_val;
        cur_sum += v as i64;
        if cur_sum > max_sum {
            max_sum = cur_sum;
        }
        if cur_sum < 0 {
            cur_sum = 0;
        }
    }
    max_sum
}

fn total_max_subarray_sum(n: usize, initial_seed: u32, min_val: i32, max_val: i32) -> i64 {
    let mut total = 0i64;
    let mut lcg = Lcg::new(initial_seed);
    for _ in 0..20 {
        let seed = lcg.next().unwrap();
        total += max_subarray_sum_fast(n, seed, min_val, max_val);
    }
    total
}

fn main() {
    let start = Instant::now();
    let result = total_max_subarray_sum(N, INITIAL_SEED, MIN_VAL, MAX_VAL);
    let elapsed = start.elapsed();
    let secs = elapsed.as_secs_f64();

    println!("Total Maximum Subarray Sum (20 runs): {}", result);
    println!("Execution Time: {:.6f} seconds", secs);
}