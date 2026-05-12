include<common.scad>;

difference() {
    panel(90, 90);

    translate([10, 90-33, 0])
    rotate([-90, 0, 0])
        #bmd_micro_converter();

    translate([90-(26/2)-5.8, 90-(31/2)-6, 0])
    rotate([-90, 0, 0])
        #neutrik_d();


    translate([90-(26/2)-5.8, 30, 0])
    rotate([-90, 0, 0])
        #neutrik_d();

    translate([(26/2)+5.8, 30, 0])
    rotate([-90, 0, 0])
        #neutrik_d();

    translate([45, 30, 0])
    rotate([-90, 0, 0])
        #neutrik_d();

}
