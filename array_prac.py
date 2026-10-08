nums = [17, 42, 8, 99, 3]
print(nums[0])
print(nums[:3])
for i, n in enumerate(nums):
    print(i, n)
# **********************************#

print("**************** Exercise 1 *******************")
scores = [88, 72, 95, 60, 100, 84]
print(scores[0])
print(scores[-1])
print(scores[1:5])
for index, score in enumerate(scores):
    if score >= 85:
        print(index, score)

# Module 3 Reverse Array


def reverse(arr):
    left = 0
    right = len(arr) - 1

    while left < right:
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr


reverse_array = reverse([1, 2, 3, 4, 5])
print(reverse_array)


# Module 3 Palindrome
def palindrome(arr):
    left = 0
    right = len(arr) - 1

    while left < right:
        if arr[left] != arr[right]:
            return False
        left += 1
        right -= 1
    return True


is_palindrome = palindrome([1, 2, 3, 9, 1])
print(is_palindrome)


# Module 3  Array Sum


def sum_array(arr, target):
    left = 0
    right = len(arr) - 1
    while left < right:
        current_sum = arr[left] + arr[right]

        if current_sum == target:
            return True
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return False


is_sum_correct = sum_array([1, 3, 5, 7, 9], 100)
print(is_sum_correct)


# Module 4 Sliding Window Pattern
def max_sum_k(arr, k):
    window_sum = sum(arr[:k])
    best = window_sum

    for right in range(k, len(arr)):
        window_sum += arr[right]
        window_sum -= arr[right - k]
        best = max(best, window_sum)
    return best


def max_average(nums, k):
    current_sum = sum(nums[:k])
    max_sum = current_sum

    for i in range(k, len(nums)):
        current_sum += nums[i] - nums[i - k]
        if current_sum > max_sum:
            max_sum = current_sum
    return max_sum / k


find_max_average = max_average([1, 12, -5, -6, 50, 3], 4)
# find_max_average = max_average([5, 5, 5, 5], 2)
print(find_max_average)
