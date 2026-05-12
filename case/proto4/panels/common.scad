inner_width=90;
inner_height=90;
inner_length=145;

bevel=5;
bar=6;
barw=4;
thick=8;

width=inner_width+(2*(thick));
height=inner_height+(2*(thick));
length=inner_length+(2*(thick));

screw_offset=3.4;

include<../../lib/components.scad>;

module panel(w,h) {
    difference() {
        translate([0.1, 0.1, 0])
        shell([w-0.2, h-0.2, thick-barw], 1.5, center=false);

        translate([screw_offset, screw_offset, 0])
            screwhole(2.5, 4.5, 8, 2);

        translate([screw_offset, h-screw_offset, 0])
            screwhole(2.5, 4.5, 8, 2);
        translate([w-screw_offset, screw_offset, 0])
            screwhole(2.5, 4.5, 8, 2);

        translate([w-screw_offset, h-screw_offset, 0])
            screwhole(2.5, 4.5, 8, 2);
    }
}

module bmd_micro_converter() {
    cube([46, 60, 25]);

    translate([14, 0, 12.5])
    rotate([90, 0, 0])
    cylinder(r=13/2, h=20, $fn=50);

    translate([14+18, 0, 12.5])
    rotate([90, 0, 0])
    cylinder(r=13/2, h=20, $fn=50);

}

module neutrik_d() {
    rotate([90, 0, 0])
    cylinder(r=24/2, h=20, $fn=50);

    translate([19/2, 0, -24/2])
    rotate([90, 0, 0])
        cylinder(r=3.5/2, h=20, $fn=50);

    translate([-19/2, 0, 24/2])
    rotate([90, 0, 0])
        cylinder(r=3.5/2, h=20, $fn=50);

    translate([0, -10, 0])
    cube([26, 1, 31], center=true);
}