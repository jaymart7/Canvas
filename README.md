# Canvas

Features:
  - Draw Lines and Box 
  - Fill character

// INPUT
        // @int width, height
        Canvas c = new Canvas(18, 10);

        // @param int ( X and Y axis -> X and Y axis)
        c.draw(3,4, 10, 4); // Horizontal Line
        c.draw(6, 1, 6, 5); // Vertical Line
        c.draw(2,0,10,7); // Box

        /*
        @param int (X and Y axis)
        @param char character to fill
        */
        c.fill(3,6, 'o'); // Fill

        // @return String
        String output = c.drawCanvas();

        System.out.println(output);
        
// OUTPUT
--------------------\n
|  xxxxxxxxx       |\n
|  x   x   x       |\n
|  x   x   x       |\n
|  x   x   x       |\n
|  xxxxxxxxx       |\n
|  xoooxooox       |\n
|  xooooooox       |\n
|  xxxxxxxxx       |\n
|                  |\n
|                  |\n
--------------------
