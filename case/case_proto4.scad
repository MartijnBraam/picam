// Show modules
show_modules=true;

display_width=121;
display_height=77.6;

size_x=display_width+17;
size_y_rear=16.8;
size_y_front=25;
size_z=95;
bevel=8;

case_screw_offset=5.2;


include<components.scad>;


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

module case() {
    
    // Front
    translate([case_width/2, 0, case_height/2])
    rotate([-90, 0, 0])
        difference() {
        shell([case_width, case_height, 8], 10);
            
        }
    // Sides
    difference() {
        translate([case_width/2, 0, case_height/2])
        rotate([-90, 0, 0])
            shell([case_width, case_height, 100], 10, 8);
        
        translate([-20, 60, -20])
        rotate([5, 0, 0])
            cube([case_width+40, 100, case_height+40]);
        
        // Side I/O
        translate([-5, 30, case_height/2-1])
        rotate([90, 0, 90])
            shell([27, 55, 30], 6);
        
        // Top I/O
        translate([case_width/2+17, 30, case_height-15])
            shell([50, 20, 30], 6);

            
        // Bottom air hole
        translate([32, 30, -0.1])
            shell([20, 20, 30], 6);

    }
    
    // Back
    if ($preview && show_modules) {
        translate([(case_width-display_width)/2, 50, 85])
        rotate([0, 96, -90])
            waveshare_with_pi();
    }
    
}

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

        }
        screwhole(2.5, 2.5, 8);
    }
}


module io_holes() {
    
    side_depth=20;
    // Side I/O
    translate([size_x-15, side_depth/2-6, size_z/2-1])
    rotate([90, 0, 90])
        shell([side_depth, 55, 30], 6);

    top_depth=20;
    // Top I/O
    translate([size_x/2-17, top_depth/2-6, size_z-15])
        shell([50, top_depth, 30], 6);
    
    // Audio board access
    audio_x=35;
    difference() {
        translate([-60+audio_x, -10, (size_z/2)-35])
            rcube(60, 60, 70, 10);
        
        translate([0, -size_y_rear, 0])
            cube([size_x, size_y_rear, size_z]);
    }

}

module case_screws() {
        translate([case_screw_offset, 0, case_screw_offset])
        rotate([90, 0, 0])
            union() {
                insert(2.5, 4, 8);
                screwhole(2.5, 4.5, 8, 2);
            }
        translate([case_screw_offset, 0, size_z-case_screw_offset])
        rotate([90, 0, 0])
            union() {
                insert(2.5, 4, 8);
                screwhole(2.5, 4.5, 8, 2);
            }
        translate([size_x-case_screw_offset, 0, case_screw_offset])
        rotate([90, 0, 0])
            union() {
                insert(2.5, 4, 8);
                screwhole(2.5, 4.5, 8, 2);
            }
        translate([size_x-case_screw_offset, 0, size_z-case_screw_offset])
        rotate([90, 0, 0])
            union() {
                insert(2.5, 4, 8);
                screwhole(2.5, 4.5, 8, 2);
            }
   
}

module case_front() {
    color("#373")
    difference() {
        // Outer shell
        translate([0, -size_y_front, 0])
            rcube(size_x, size_y_front*2, size_z, bevel, fn=90);
        translate([-0.5, -size_y_front*2, -0.5])
            cube([size_x+1, size_y_front*2, size_z+1]);

        // Open up the inside
        wall=6;
        wall_front=4;
        difference() {
            translate([wall, -size_y_front-wall_front, wall])
                rcube(size_x-wall*2, size_y_front*2, size_z-wall*2, bevel, fn=40);
            
            // Sensor mount (additive part)
            translate([size_x/2, size_y_front, size_z/2])
            rotate([90, 0, 0])
                cam4_mountbody_add();
        }
        
        // Tripod mount
        translate([size_x/2, 10, 0])
        rotate([180, 0, 0])
            insert(0, 7.15, 6);

        // Sensor mount (substractive part)
        translate([size_x/2, size_y_front, size_z/2])
        rotate([90, 0, 0])
            cam4_mountbody();
        
        io_holes();
        case_screws();
    }
}

module case_rear() {
    color("#555")
    difference() {
        // Outer shellw
        translate([0, -size_y_rear, 0])
            rcube(size_x, size_y_rear*2, size_z, bevel, fn=90);
        translate([-0.5, 0, -0.5])
            cube([size_x+1, size_y_rear*2, size_z+1]);
        
        // Display cutout
        translate([size_x/2,0.5,size_z/2])
            rotate([90, 0, 0])
            ccube([display_width, display_height, size_y_rear+1]);
        
        // Display touch flex cutout
        cutout_z=2;
        translate([size_x/2+34, -size_y_rear+1.01, 4.8+cutout_z])
            cube([10, size_y_rear-1, 2], center=false);
        
        io_holes();
        case_screws();
    }
    
    // Display
    translate([0, 0, 2.5])
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
        
        if ($preview && show_modules) {
            translate([size_x/2, -15.7, size_z/2])
                rotate([90, 0,0])
                color("#333")
                import("5INCH-DSI-LCD-C.stl");
        }
    }
   
}

    //case_rear();
    case_front();