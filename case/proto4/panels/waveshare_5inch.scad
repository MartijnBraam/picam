include<common.scad>;

display_width=121;
display_height=77.6;
size_x=145;
size_z=90;

module displaymount(r) {
    difference() {
        rotate([0, 0, r])
        union() {
            color("#ccc")
            cylinder(h=3, r=5, $fn=90);

            color("#ccc")
            translate([0, -5, 0])
                cube([10, 10, 3]);

            color("#ccc")
            translate([-5, -10, 0])
                cube([10, 10, 3]);

            color("#aaa")
            translate([-5, -10, 0])
                cube([10, 4.5, 15]);

            color("#aaa")
            translate([5.5, -5, 0])
                cube([4.5, 10, 15]);

        }
        screwhole(2.5, 2.5, 8);
    }
}

difference() {
    panel(145, 90);

    translate([size_x/2,size_z/2, -5])
    rotate([0, 0, 0])
        ccube([display_width, display_height, 10]);

    // Display touch flex cutout
    cutout_z=2;
    translate([size_x/2+34, 3.3,3])
        rotate([-90, 0, 0])
        #cube([10, 10-1, 3], center=false);


}
difference() {
    translate([0, 0, -13])
    rotate([-90, 0, 0])
    union() {
        translate([(size_x/2)-(display_width/2)+4, 0, 11.5])
        rotate([90, 0, 0])
            displaymount(270);
        translate([(size_x/2)+(display_width/2)-4, 0, 11.5])
        rotate([90, 0, 0])
            displaymount(0);
        translate([(size_x/2)-(display_width/2)+4, 0, 79.5])
        rotate([90, 0, 0])
            displaymount(180);
        translate([(size_x/2)+(display_width/2)-4, 0, 79.5])
        rotate([90, 0, 0])
            displaymount(90);

        if ($preview && false) {
            translate([size_x/2, -15.7, 47.4])
                rotate([90, 0,0])
                color("#333")
                import("5INCH-DSI-LCD-C.stl");
        }
    }

    translate([0, 84, -15])
        cube([size_x, 10, 15]);
}

