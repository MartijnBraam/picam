// Show modules
show_modules=true;

display_width=120.7;
case_width=display_width+16;
case_height=94;
case_screw_offset=5.2;
logo_inset=3;

split_pos=32.9;

include<components.scad>;


module logo() {
    difference() {
    linear_extrude(height=5)
        import("logo.svg");
        
        translate([2, 2, 0])
        scale([0.98, 0.98, 1])
        linear_extrude(height=5)
        import("logo.svg");

    }
}

module display() {
    thick=5;
    dw=120.7;
    dh=77.2;

    if ($preview && show_modules) {
        translate([7, 10, 0.98])
            rotate([0,0,0])
            waveshare5inch();
    }

    difference() {
        cube([cam_w, cam_l, thick]);
        
        translate([cam_w/2-2, cam_l/2, -0.01])
        linear_extrude(1, scale=[0.85, 0.90])
            square([dh, dw], center=true);
        
        translate([thick+2, 10, 0.9])
            cube([dh+30, dw+0.3, 10]);
    }
    
    translate([5, 10, 5])
        cube([2, dw, 5]);
}

module side_io() {
    thick=5;
    dw=10;
    dh=10;
    difference() {
        cube([cam_w, cam_l, thick]);
        
        translate([cam_w/2-20, cam_l/2, -0.01])
        linear_extrude(1, scale=[0.85, 0.90])
            square([dh, dw], center=true);
        
        translate([thick+2, 10, 0.9])
            cube([dh+30, dw+0.3, 10]);
    }
}


module top() {
    thick=7;
    difference() {
        translate([0,0,0])
            cube([cam_w, cam_l, thick]);
                
        // LCD panel cutout
        translate([cam_w-11,8,5.7])
            cube([10, 123, 10]);
        
        // Top mounting holes
        translate([cam_w/2,cam_l/3,-0.01])
        rotate([180, 0, 0])
            insert(0, 7.15, 6);
        
        translate([cam_w/2,cam_l/2,-0.01])
        rotate([180, 0, 0])
            insert(0, 7.15, 6);

        translate([cam_w/2,cam_l/3*2,-0.01])
        rotate([180, 0, 0])
            insert(0, 7.15, 6);
    }
}

module case() {
    
    // Front
    difference() {
        intersection() {
            rotate([90, 0, 0])
                mount_cs(width=case_width, height=case_height);
            
            translate([case_width/2, 0, case_height/2])
            rotate([-90, 0, 0])
                shell([case_width, case_height, 30], 10);
        }
        
        // Logo inset
        translate([23.4, logo_inset, 1.5])
        rotate([90, 0, 0])
        scale([0.45, 0.45 , 1])
            logo();
    }
    
    // Sides
    difference() {
        translate([case_width/2, 0, case_height/2])
        rotate([-90, 0, 0])
            shell([case_width, case_height, 100], 10, 8);
        
        // Logo inset
        translate([23.4, logo_inset, 1.5])
        rotate([90, 0, 0])
        scale([0.45, 0.45 , 1])
            logo();
        
        translate([-20, 50.5, -20])
        rotate([0, 0, 0])
            cube([case_width+40, 100, case_height+40]);
                
        // Side I/O
        translate([-5, 30, case_height/2-1])
        rotate([90, 0, 90])
            shell([27, 55, 30], 6);
        
        // Audio I/O
        translate([case_width-20, 23.1, case_height/2-1])
        rotate([90, 0, 90])
            shell([30, 70, 30], 6);

        
        // Top I/O
        translate([case_width/2+17, 30, case_height-15])
            shell([50, 20, 30], 6);

        // Tripod mount
        translate([case_width/2, 20, 0])
        rotate([180, 0, 0])
            insert(0, 7.15, 6);
            
        // Bottom air hole
        translate([32, 30, -0.1])
            shell([20, 20, 30], 6);

    }
    
    // Back
    if ($preview && show_modules) {
        translate([(case_width-display_width)/2, 50, 85])
        rotate([0, 90, -90])
            waveshare_with_pi();
    }
    
}

module case_a() {
    difference() {
        case();
        
        translate([-5, split_pos, -5])
            cube([case_width+10, 100, case_height+10]);
        
        // Case screws
        translate([6, split_pos, 6])
        rotate([-90, 0, 0])
            insert(2.5, 4, 8);
        translate([6, split_pos, case_height-6])
        rotate([-90, 0, 0])
            insert(2.5, 4, 8);
        translate([case_width-6, split_pos, 6])
        rotate([-90, 0, 0])
            insert(2.5, 4, 8);
        translate([case_width-6, split_pos, case_height-6])
        rotate([-90, 0, 0])
            insert(2.5, 4, 8);

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

module case_b() {
    difference() {
        union() {
            
            difference() {
                case();
                
                translate([-5, -0.01, -5])
                    cube([case_width+10, split_pos+0.01, case_height+10]);
                
                dfh=case_height-15;
                translate([case_width/2, split_pos+17.49, (dfh/2)+7])
                    cube([display_width+1, 35, dfh], center=true);
            }
            
            rotate([0, 0, 0])
            union() {
                zo = 5;
                yo = 36.5;
                translate([(case_width/2)-(display_width/2)+4, yo, 7.5+zo])
                rotate([90, 0, 0])
                    displaymount(270);
                translate([(case_width/2)+(display_width/2)-4, yo, 7.5+zo])
                rotate([90, 0, 0])
                    displaymount(0);
                translate([(case_width/2)-(display_width/2)+4, yo, 75.5+zo])
                rotate([90, 0, 0])
                    displaymount(180);
                translate([(case_width/2)+(display_width/2)-4, yo, 75.5+zo])
                rotate([90, 0, 0])
                    displaymount(90);

            }
        }
        
        // Case screws
        translate([case_screw_offset, split_pos, case_screw_offset])
        rotate([-90, 0, 0])
            screwhole(2.5, 4, 8, 2);
        translate([case_screw_offset, split_pos, case_height-case_screw_offset])
        rotate([-90, 0, 0])
            screwhole(2.5, 4, 8, 2);
        translate([case_width-case_screw_offset, split_pos, case_screw_offset])
        rotate([-90, 0, 0])
            screwhole(2.5, 4, 8, 2);
        translate([case_width-case_screw_offset, split_pos, case_height-case_screw_offset])
        rotate([-90, 0, 0])
            screwhole(2.5, 4, 8, 2);
        
        // Display touch flex
        translate([12.4+18, 47, 5.5])
            cube([10, 20, 3], center=true);
    }
}


module split() {
    difference() {
        case_b();
            
        translate([-0.5, 0, -0.5])
        cube([case_width/2+1, 100, case_height+1]);
    }
}

case_a();
//case_b();
/*
translate([0,0 , 60])
rotate([-95, 0, 0])
case_b();
*/