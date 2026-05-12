include<common.scad>;

difference() {
    panel(145, 90);

    translate([145/2, 90/2, 4.05])
        insert(0, 7, 8);

    translate([145/4, 90/2, 4.05])
        insert(0, 7, 8);

    translate([145/4*3, 90/2, 4.05])
        insert(0, 7, 8);

    translate([145/4*3, 90/4, 4.05])
        insert(0, 4, 8);

    translate([145/4*3, 90/4*3, 4.05])
        insert(0, 4, 8);

    translate([145/4, 90/4, 4.05])
        insert(0, 4, 8);

    translate([145/4, 90/4*3, 4.05])
        insert(0, 4, 8);


    translate([145/2, 90/4, 4.05])
        insert(0, 4, 8);

    translate([145/2, 90/4*3, 4.05])
        insert(0, 4, 8);
}
