flange_distance=19.25;

include<components.scad>;

module cam4_mount(hole=40, hfn=4) {
    size=62;
    screw_spacing=52;

    difference() {
        linear_extrude(3) {
            rsquare2([size, size], 5);
        }
        translate([screw_spacing/2, screw_spacing/2, 0])
            screwhole(2.5, 5, 8, 2);
        translate([-screw_spacing/2, screw_spacing/2, 0])
            screwhole(2.5, 5, 8, 2);
        translate([screw_spacing/2, -screw_spacing/2, 0])
            screwhole(2.5, 5, 8, 2);
        translate([-screw_spacing/2, -screw_spacing/2, 0])
            screwhole(2.5, 5, 8, 2);

        children();
        
        translate([0, 0, -1])
        rotate([0, 0, 45])
            cylinder(r=hole/2, h=10, $fn=hfn);
        
        translate([48/2, 0, -4])
            cylinder(r=1.5/2, h=10, $fn=40);

    }
    children();
        
    if($preview) {
        hole = size - 4;
        color("red")
        translate([0, 0 ,-5])
        union() {
            shell([hole+4, hole+4, 5], 1, 2);
            translate([hole/2-1, hole/2-1, 0])
                cylinder(r=7, h=7);
            translate([-hole/2+1, hole/2-1, 0])
                cylinder(r=7, h=7);
            translate([hole/2-1, -hole/2+1, 0])
                cylinder(r=7, h=7);
            translate([-hole/2+1, -hole/2+1, 0])
                cylinder(r=7, h=7);
        }
    }
}


module mount_sensor() {
    rotate(30) {
        offset=38;
        translate([offset/2, offset/2, -0.01])
        rotate([180, 0, 0])
            insert(2.5, 4, 3);
        translate([-offset/2, offset/2, -0.01])
        rotate([180, 0, 0])
            insert(2.5, 4, 3);
        translate([-offset/2, -offset/2, -0.01])
        rotate([180, 0, 0])
            insert(2.5, 4, 3);
        translate([offset/2, -offset/2, -0.01])
        rotate([180, 0, 0])
            insert(2.5, 4, 3);
    }
}

module mount_mft(hole=25, height=7) {
    // z=0 of this module is the flange
    
    inset=4;
    screw_r=1.7/2;
    rectangle_length=48;
    pin_height=2;
    
    translate([0, 0, -height-pin_height])
    union() {
        // Indicator pin
        if (false) {
        rotate([0, 0, 161])
        translate([47/2, 0, height])
            cylinder(r=1.4/2, h=pin_height, $fn=40);
        }
                
        difference(){
            union() {
                cylinder(r=54/2, h=height, $fn=180);
                translate([0, 0, 3])
                    fillet(54/2, 4, $fn=90);
            }
                
            translate([0, 0, -1])
            cylinder(r=hole/2, h=height, $fn=180);
            
            // Inset area
            translate([0, 0, height-inset-0.05])
                cylinder(r=42/2, h=inset+0.1, $fn=180);
            
            // Locking pin
            rotate([0, 0, 0])
            translate([48/2, 0, height-5])
                cylinder(r=5/2, h=height, $fn=40);
            translate([48/2, 0, -4])
                cylinder(r=1.5/2, h=height, $fn=40);

            rotate([0, 0, -90])
            translate([0, 3+(48/2), height-1])
                cube([5, 6, 2.1], center=true);
            rotate([0, 0, -90])
            translate([0, 3+(53/2), height-1])
                cube([8, 6, height*2], center=true);

            


            // Rectangular inset cutouts
            rotate([0, 0, 90])
            rotate([0, 0, -90])
            translate([0, rectangle_length/4, height-(inset/2)])
                cube([12, rectangle_length/2, inset+0.1], center=true);
            rotate([0, 0, -26.5])
            rotate([0, 0, -90])
            translate([0, rectangle_length/4, height-(inset/2)])
                cube([12, rectangle_length/2, inset+0.1], center=true);
            rotate([0, 0, 205])
            rotate([0, 0, -90])
            translate([0, rectangle_length/4, height-(inset/2)])
                cube([12, rectangle_length/2, inset+0.1], center=true);

            // Screws
            rotate([0, 0, 50])
            translate([48/2, 0, height-5])
                cylinder(r=screw_r, h=5+0.1, $fn=8);
            rotate([0, 0, 180-50])
            translate([48/2, 0, height-5])
                cylinder(r=screw_r, h=5+0.1, $fn=8);
            rotate([0, 0, -50])
            translate([48/2, 0, height-5])
                cylinder(r=screw_r, h=5+0.1, $fn=8);
            rotate([0, 0, -180+50])
            translate([48/2, 0, height-5])
                cylinder(r=screw_r, h=5+0.1, $fn=8);
        }
    }
}

module fillet(r, size, $fn) {
    rotate_extrude(convexity = 10, $fn=$fn)
    translate([r, 0, 0])
        difference() {
            square(size);
            translate([size, size])
            circle(size, $fn=$fn);
        }
}

module imx290() {
    // sensor area
    color("#444")
    translate([0, 0, 0.5/2])
        cube([12, 9, 0.5], center=true);
    
    // Flange distance indicator
    color("#00FF0055")
    translate([0, 0, 0])
        cube([30, 1, flange_distance]);
    
    // ir cut mounting thingy
    color("#333")
    difference() {
        translate([0, 0, 0.1])
        cube([18, 18, 0.2], center=true);
        
        translate([0, 0, 0.1])
        cube([14, 14, 0.3], center=true);
    }

    translate([-16, -16, -1.6])
    difference() {
        // PCB
        color("green")
            cube([32, 32, 1.6]);
                
        // Screw holes
        translate([2.5, 2.5, -0.2])
            cylinder(r=2.5/2,h=2, $fn=15);
        translate([2.5+27, 2.5, -0.2])
            cylinder(r=2.5/2,h=2, $fn=15);
        translate([2.5, 2.5+27, -0.2])
            cylinder(r=2.5/2,h=2, $fn=15);
        translate([2.5+27, 2.5+27, -0.2])
            cylinder(r=2.5/2,h=2, $fn=15);
    }
}

module imx290_mount(height) {
    a_height=5;
    b_height=height-a_height;
    
    difference() {
        translate([0, 0, a_height/2])
        cube([17, 17, a_height], center=true);
        
        translate([0, 0, a_height/2-0.1])
        cube([14, 14, a_height+0.4], center=true);
    }
    
    translate([0, 0, a_height]) {
        difference() {
            ccube([32, 32, b_height]);
            
            translate([27/2, 27/2, -0.01])
            rotate([180, 0, 0])
                insert(2.5, 4, 4.2);
            translate([-27/2, 27/2, -0.01])
            rotate([180, 0, 0])
                insert(2.5, 4, 4.2);
            translate([-27/2, -27/2, -0.01])
            rotate([180, 0, 0])
                insert(2.5, 4, 4.2);
            translate([27/2, -27/2, -0.01])
            rotate([180, 0, 0])
                insert(2.5, 4, 4.2);

            translate([0, 0, -0.05])
            rotate([0, 0, 45])
            cylinder(h=b_height+0.1, r1=14/2, r2=35/2, $fn=4);
        }
    }

}

difference() {
    cam4_mount(hole=40) {
        translate([0, 0, 10])
        union() {
            mount_mft(height=8);
            
            //translate([0, 0, -flange_distance])
            //imx290();
                
                
            //translate([0, 0, -flange_distance])
            //    imx290_mount(10);
        }
    }
    
    mount_sensor();
    
                translate([0, 0, 2])
            rotate([0, 0, -90])
            translate([0, 3+(53/2), 8-1])
                cube([8, 6, 8*2], center=true);

}