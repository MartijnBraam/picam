include<common.scad>;

module cam4_mountbody() {
        size=62;
        hole=size-4;
        screw_spacing=52;
        margin=0.3;


        linear_extrude(3) {
            rsquare2([size+margin*2, size+margin*2], 5);
        }

        translate([screw_spacing/2,screw_spacing/2, 2.99])
        rotate([180, 0, 0])
            insert(2.5, 4, 8);
        translate([-screw_spacing/2,screw_spacing/2, 2.99])
        rotate([180, 0, 0])
            insert(2.5, 4, 8);
        translate([screw_spacing/2,-screw_spacing/2, 2.99])
        rotate([180, 0, 0])
            insert(2.5, 4, 8);
        translate([-screw_spacing/2,-screw_spacing/2, 2.99])
        rotate([180, 0, 0])
            insert(2.5, 4, 8);


        difference() {
            linear_extrude(20) {
                rsquare2([hole, hole], 5);
            }

            translate([hole/2-1, hole/2-1, 0])
                cylinder(r=7, h=20);
            translate([-hole/2+1, hole/2-1, 0])
                cylinder(r=7, h=20);
            translate([hole/2-1, -hole/2+1, 0])
                cylinder(r=7, h=20);
            translate([-hole/2+1, -hole/2+1, 0])
                cylinder(r=7, h=20);
        }
}

module cam4_mountbody_add() {
        size=62;
        hole=size-4;
        screw_spacing=52;
        margin=0.3;

        union() {
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

difference() {
    union() {
        panel(90, 90);
        
        translate([45, 45, thick-barw])
            rotate([180, 0, 0])
            
        cam4_mountbody_add();
    }
    translate([45, 45, thick-barw])
    rotate([180, 0, 0])
        cam4_mountbody();
}
