use std::time::Instant;

#[inline(always)]
fn lcg_next(state: &mut u32) -> u32 {
    const A: u32 = 1664525;
    const C: u32 = 1013904223;
    *state = state.wrapping_mul(A).wrapping_add(C);
    *state
}

#[inline(always)]
fn max_subarray_sum(n: usize, seed: u32, min_val: i128, max_val: i128) -> i128 {
    let mut state = seed;
    let range_len_i128 = max_val - min_val + 1;
    // Assume valid inputs where max_val >= min_val
    let range_len_u128 = range_len_i128 as u128;

    // Kadane's algorithm in a single pass, streaming values from LCG
    let mut max_so_far: i128;
    let mut current_max: i128;

    // First element initializes Kadane's state
    let v0 = lcg_next(&mut state) as u128;
    let x0 = (v0 % range_len_u128) as i128 + min_val;
    current_max = x0;
    max_so_far = x0;

    // Remaining elements
    let mut i = 1usize;
    while i < n {
        let v = lcg_next(&mut state) as u128;
        let x = (v % range_len_u128) as i128 + min_val;
        let sum = current_max + x;
        current_max = if sum > x { sum } else { x };
        if current_max > max_so_far {
            max_so_far = current_max;
        }
        i += 1;
    }

    max_so_far
}

#[inline(always)]
fn total_max_subarray_sum(n: usize, initial_seed: u32, min_val: i128, max_val: i128) -> i128 {
    let mut total_sum: i128 = 0;
    let mut seed_state = initial_seed;
    let mut i = 0;
    while i < 20 {
        let seed = lcg_next(&mut seed_state);
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
        i += 1;
    }
    total_sum
}

fn main() {
    // Parameters
    let n: usize = 10000;
    let initial_seed: u32 = 42;
    let min_val: i128 = -10;
    let max_val: i128 = 10;

    // Timing the function
    let start_time = Instant::now();
    let result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    let duration = start_time.elapsed();
    let seconds = duration.as_secs_f64();

    println!("Total Maximum Subarray Sum (20 runs): {}", result);
    println!("Execution Time: {:.6} seconds", seconds);
}