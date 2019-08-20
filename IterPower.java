


public class IterPower {
	public static void main(String[] args) {
		System.out.println(iterPower(10, 4));
	}

	public static int iterPower(int base, int exp) {
		int result = 1;
		while (exp > 0) {
			result *= base;
			exp -= 1;
		}
		return result;
	}
}