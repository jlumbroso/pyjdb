public class Test {
    static int glob;
    public static void main(String[] args) {
	int x = 10;
	glob = 2;
	System.out.println(glob);
	x = testfunc(x, glob, "adding");
	while(x > 0) x--;
	System.out.println(x);
    }
    public static int testfunc(int arg1, int arg2, String arg3) {
	int local1 = 0;
	local1 = arg1 + arg2;
	System.out.println(local1);
	System.out.println(arg3);
	return local1;
    }
}