/******************************************************************************
    IterPower Java example to illustrate variable name clustering,
    after E. Glassman (2016)

    See Fig 1-6 and Fig 1-7:
       https://eglassman.github.io/papers/elg-thesis.pdf

    Compile with -g debug flag to get debugging information, i.e.:
        javac -g IterPower.java
******************************************************************************/


public class IterPower {
	public static void main(String[] args) {
	    // Default values
	    int base = 10;
	    int exp = 4;

        // Parse command-line arguments
	    if (args.length > 0)
	        base = Integer.parseInt(args[0]);
	    if (args.length > 1)
	        exp = Integer.parseInt(args[1]);

        // Call the function
		System.out.println(iterPower(base, exp));
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