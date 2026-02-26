// Show camera mount
show_front=true;

// Show display
show_left=true;

// Show I/O panel
show_right=true;

// Show rear panel
show_rear=true;

// Show mounting plate
show_bottom=true;

// Show top plate
show_top=true;

// Show modules
show_modules=true;

// Camera outder dimensions
cam_w=90;
cam_l=140;

module picam_cs() {
    // Raspberry Pi HQ camera module with C mount
    offset=4;
    pcb=1.4;
    translate([-38/2, -38/2, -pcb])
    union() {
        // PCB
        difference() {
            color("#090")
                cube([38, 38, pcb]);
            translate([offset, offset, 3])
                cylinder(h=10, r=2.5/2, center=true, $fn=180);
            translate([38-offset, offset, 3])
                cylinder(h=10, r=2.5/2, center=true, $fn=180);
            translate([38-offset, 38-offset, 3])
                cylinder(h=10, r=2.5/2, center=true, $fn=180);
            translate([offset, 38-offset, 3])
                cylinder(h=10, r=2.5/2, center=true, $fn=180);
        }
        // Lens mount
        color("#333")
        difference() {
            union() {
                translate([38/2, 38/2, 11.4/2+pcb])
                    cylinder(h=11.4, r=36/2, center=true);
                translate([38/2, 38/2, 11.4+pcb+(5.8/2)])
                    cylinder(h=5.8, r=30.75/2, center=true);
            }
            translate([38/2, 38/2, pcb+(17.2/2)+0.1])
                cylinder(h=17.2, r=22.4/2, center=true);
        }
        // Focus ring clamp
        color("#333")
        translate([38/2,38,pcb+11.4-(5/2)])
            cube([10.16, 5, 5.02], center=true);
        
        // Lens cap
        color("#555")
        translate([38/2, 38/2, pcb+17.2+5/2])
            cylinder(h=5, r=30/2, center=true);

    }
}

module waveshare5inch() {
    // WaveShare 5" DSI monitor [28146]
    w=120.7;
    h=77.2;
    d=13.4;
    pcb=9.4;
    
    // Digitizer
    color("#000")
    cube([h, w, 1]);
    
    // IPS area
    color("#F00")
    translate([3.1,(120.7-109)/2,-0.01])
    cube([65.8, 109, 0.01]);
    
    // Space occupied by PCB and electronics
    color("#090")
    translate([0,0,1])
    cube([77.2, 120.7, pcb-1]);
    
    // Mounts
    md = d-pcb;
    hoff = (h-68)/2;
    woff = (w-113)/2;
    translate([hoff, woff,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);
    translate([h-hoff, woff,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);
    translate([h-hoff, w-woff,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);
    translate([hoff, w-woff,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);
        
    // DSI connector
    color("#eee")
    translate([h/2-20.6/2, w-5, pcb])
        cube([20.6,3, 5.5]);
}

module insert(size, od, l) {
    translate([0,0,-0.1])
        cylinder(center=true, r=od/2+0.4, h=0.2,$fn=180);
    translate([0,0,-0.1-(l/2)])
        cylinder(center=true, r=od/2, h=l,$fn=180);
}

module screwhole(size, head_size) {
    hd=10;
    d=2;
    translate([0,0,hd/2])
        cylinder(center=true, r=head_size/2+0.4, h=hd, $fn=180);
    
    translate([0,0,-d/2])
        cylinder(center=true, r=size/2+0.4, h=hd, $fn=180);    
}

module mount_cs() {
    thick=8;
    inset=22.5;
    if($preview && show_modules) {
        translate([cam_w/2, cam_w/2, -inset])
            picam_cs();
    }
    translate([0,0,-thick])
        difference () {
        union() {
            cube([cam_w, cam_w, thick]);
            translate([cam_w/2, cam_w/2, (inset-thick)/2-(inset-thick)])
            rotate([0,0, 45])
            cylinder($fn=4, h=inset-thick, r1=30, r2=42, center=true);
        }
        
        // Lens hole
        translate([cam_w/2, cam_w/2, 2.5])
            cylinder(h=inset+thick+10, r=38/2, center=true, $fn=180);
            
        // Inset front
        translate([cam_w/2, cam_w/2, thick/2+0.01])
            cylinder(h=thick, r1=23, r2=32, center=true, $fn=180);
        
        // Sensor screw holes
        soff = (38/2)-4;
        translate([cam_w/2-soff, cam_w/2-soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);
        translate([cam_w/2+soff, cam_w/2-soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);
        translate([cam_w/2-soff, cam_w/2+soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);
        translate([cam_w/2+soff, cam_w/2+soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);

        
        // Hole for lens focus clamp
        translate([cam_w/2,cam_w/2+21,(-inset/2)-1])
            cube([12, 8, inset], center=true);
        }        
}

module cpu_board() {
    color("#090")
    translate([6,0,-1.6])
    cube([68, 120, 1.6]);
}

module bottom() {
    thick=7;
    spacer=5;
    
    if ($preview && show_modules) {
        translate([0,0,thick+1.6+spacer])
            cpu_board();
    }
    
    difference() {
        translate([0,0,0])
            cube([cam_w, cam_l, thick]);
        
        // Prevent bottom plate from sticking through the display chamfer
        translate([cam_w, 10.3, 0])
        rotate([45, 0, 90])
            cube([120.7, 20, 20]);
        
        // Bottom mounting holes
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

module rear() {
    thick=5;
    difference() {
        cube([cam_w, cam_w, thick]);
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
    // Bottom
    if (show_bottom)
        bottom();
    
    // Front
    if (show_front)
    rotate([90, 0, 0])
        mount_cs();
    
    // Side
    if (show_left)
    translate([cam_w, 0, 0])
    rotate([0,-90,0])
        display();
    
    // Other side
    if (show_right)
    translate([0,cam_l,0])
    rotate([0,-90,180])
        side_io();
    
    // Rear
    if (show_rear)
    translate([0,cam_l,0])
    rotate([90,0,0])
        rear();
    
    // Top
    if (show_top)
    translate([0, cam_l, cam_w])
    rotate([180 ,0 ,0])
        top();
}

module case_chamfered() {
    c=8;
    difference() {
        case();
        
        translate([0, -5, -(c/2)*sqrt(2)])
        rotate([45, 0, 90])
            cube([cam_l+10, c, c]);
        
        translate([cam_w, -5, -(c/2)*sqrt(2)])
        rotate([45, 0, 90])
            cube([cam_l+10, c, c]);

        translate([0, -5, -(c/2)*sqrt(2)+cam_w])
        rotate([45, 0, 90])
            cube([cam_l+10, c, c]);
        
        translate([cam_w, -5, -(c/2)*sqrt(2)+cam_w])
        rotate([45, 0, 90])
            cube([cam_l+10, c, c]);

        translate([-(c/2)*sqrt(2), 0, cam_w+5])
        rotate([45, 90, 0])
            cube([cam_w+10, c, c]);
            
        translate([-(c/2)*sqrt(2), cam_l, cam_w+5])
        rotate([45, 90, 0])
            cube([cam_w+10, c, c]);

        translate([-(c/2)*sqrt(2)+cam_w, cam_l, cam_w+5])
        rotate([45, 90, 0])
            cube([cam_w+10, c, c]);

        translate([-(c/2)*sqrt(2)+cam_w, 0, cam_w+5])
        rotate([45, 90, 0])
            cube([cam_w+10, c, c]);

        translate([0,0,-(c/2)*sqrt(2)])
        rotate([45, 0, 0])
            cube([cam_w+10, c, c]);

        translate([0,0,-(c/2)*sqrt(2)+cam_w])
        rotate([45, 0, 0])
            cube([cam_w+10, c, c]);
            
        translate([0,cam_l,-(c/2)*sqrt(2)])
        rotate([45, 0, 0])
            cube([cam_w+10, c, c]);

        translate([0,cam_l,-(c/2)*sqrt(2)+cam_w])
        rotate([45, 0, 0])
            cube([cam_w+10, c, c]);
    }
}

module case_bottom() {
    difference() {
        case_chamfered();
        
        // Remove top panel
        translate([0, 8, cam_w-7.01])
            cube([cam_w+10, cam_l+10, 10]);
        
        // Remove right side
        translate([-4.99, 8, 7])
            cube([10, cam_l+10, cam_w+10]);
        
        // Remove rear panel
        translate([-10-5, cam_l-9, 7])
            cube([cam_w+10, 10, cam_w+10]);
        
        // Front screw holes
        translate([10, 6, cam_w-3])
        rotate([90, 0, 0])
            screwhole(2.5, 4);
        translate([cam_w-10, 6, cam_w-3])
        rotate([90, 0, 0])
            screwhole(2.5, 4);
            
        // Bottom screw holes
        translate([2.5, 14, 5])
        rotate([180, 0, 0])
            screwhole(2.5, 4);
        translate([2.5, cam_l/2, 5])
        rotate([180, 0, 0])
            screwhole(2.5, 4);
        translate([2.5, cam_l-14, 5])
        rotate([180, 0, 0])
            screwhole(2.5, 4);

        // Display side screw holes
        translate([cam_w-3, cam_l-5, 14])
        rotate([0, 90, 0])
            screwhole(2.5, 4);
        translate([cam_w-3, cam_l-5, cam_w-14])
        rotate([0, 90, 0])
            screwhole(2.5, 4);

    }
}

case_bottom();

/*
if (show_modules) {
color("#333")
translate([25, 75+40, 100])
rotate([90, 0, 0])
cylinder(r=20, h=75, $fn=90);
}
//display();
*/