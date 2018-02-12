
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * Created by Jaymart on 09/02/2018.
 */
class Canvas {

    private String[][] matrix;
    private static final String DRAW = "x";
    private int width, height;

    public Canvas(int width, int height) {

        if (width < 1 || height < 1)
            throw new IllegalArgumentException();

        this.width = width;
        this.height = height;

        StringBuilder out = new StringBuilder();
        String w = loopString(width+2, "-");
        String space = loopString(width, " ");
        String h = IntStream.range(0, height).mapToObj(n -> "|"+space+"|\n").collect(Collectors.joining());

        out.append(w).append("\n").append(h).append(w);

        String[] perLine = out.toString().split("\n");
        matrix = new String[perLine.length][];
        for (int i=0; i<perLine.length; i++){
            matrix[i] = perLine[i].split("");
        }
    }

    public Canvas draw(int x1, int y1, int x2, int y2) {

        if (x1==x2 && y1==y2)
            throw new IllegalArgumentException();

        int lowY = y1 > y2 ? y2:y1;
        int highY = y1 > y2 ? y1:y2;
        int lowX = x1 > x2 ? x2:x1;
        int highX = x1 > x2 ? x1:x2;
        int tmp;

        // Horizontal
        tmp = lowX;
        while (tmp <= highX){
            tmp++;
            matrix[y1+1][tmp] = DRAW;
        }

        // Vertical
        tmp = lowY;
        while (tmp <= highY){
            tmp++;
            matrix[tmp][x1+1] = DRAW;
        }

        if (x1==x2 || y1==y2) return this;

        // For Rectangle

        // Horizontal
        tmp = highX;
        while (lowX <= tmp){
            tmp--;
            matrix[y2+1][tmp+2] = DRAW;
        }

        // Vertical
        tmp = highY;
        while (lowY < tmp){
            matrix[tmp][x2+1] = DRAW;
            tmp--;
        }

        return this;
    }

    public Canvas fill(int x, int y, char ch) {

        int rows = height+1;
        int columns = width+1;

        if (x+1 >= columns || y+1 >= rows)
            throw new IllegalArgumentException();

        if (!matrix[y+1][x+1].equals(" ")) return this;

        int[][] MOVES = {{1,0}, {0,-1}, {0,1}, {-1, 0}};

        Set<List<Integer>> pos = new HashSet<>(Arrays.asList(Arrays.asList(y+1, x+1))),
                seens = new HashSet<>(pos);

        while (!pos.isEmpty()) {
            pos = pos.stream().flatMap( p -> Arrays.stream(MOVES)
                    .map(dxy -> Arrays.asList( p.get(0)+dxy[0], p.get(1)+dxy[1] ) )
                    .filter(np -> !seens.contains(np)
                            && np.get(0) < rows && np.get(1) >= 0 && np.get(1) < columns
                            && matrix[np.get(0)][np.get(1)].equals(" ")) )
                    .collect(Collectors.toSet());
            seens.addAll(pos);
        }

        for (List<Integer> s : seens){
            String[] arr = s.toString().split(",");
            try {
                matrix[
                        Integer.parseInt(arr[0].replaceAll("[\\D]", ""))
                        ][
                        Integer.parseInt(arr[1].replaceAll("[\\D]", ""))
                        ]
                        = String.valueOf(ch);
            }catch (Exception e){
                System.out.println(s.toString());
            }

        }

        return this;
    }

    public String drawCanvas() {
        StringBuilder out = new StringBuilder();
        for (String[] aMatrix : matrix) {
            for (int c = 0; c < matrix[0].length; c++) {
                out.append(aMatrix[c]);
            }
            out.append("\n");
        }

        return out.toString().trim();
    }

    public static String loopString(int n, String val){
        return IntStream.range(0,n).mapToObj(operand -> val).collect(Collectors.joining());
    }
}
