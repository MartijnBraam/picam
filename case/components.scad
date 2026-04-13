module insert(size, od, l) {
    translate([0,0,-0.1])
        cylinder(center=true, r=od/2+0.4, h=0.2,$fn=180);
    translate([0,0,-0.1-(l/2)])
        cylinder(center=true, r=od/2, h=l,$fn=180);
}

module screwhole(size, head_size, l=10, o=0) {
    hd=100;
    d=2;
    translate([0,0,hd/2+o])
        cylinder(center=true, r=head_size/2+0.4, h=hd, $fn=180);
    
    translate([0,0,-d/2+o])
        cylinder(center=true, r=size/2+0.4, h=l, $fn=180);    
}

module rsquare2(size, radius) {
  x = size.x - radius * 2;
  y = size.y - radius * 2;

  assert(radius < size.x / 2, "Radius must be less than half the height");
  assert(radius < size.y / 2, "Radius must be less than half the width");

  offset(r = radius, $fn=90) square([ x, y ], center = true);
}

module rcube(x, y, z, r) {
    minkowski()
    {
        translate([r,r,r]) cube([x-2*r,y-2*r,z-2*r]);
        sphere(r=r);
    }
}

module ccube(pos) {
    translate([0, 0, pos[2]/2])
        cube(pos, center=true);
}

module shell(size, radius, wall=0) {
    linear_extrude(size.z, convexity=11)
        if (wall > 0) {
            difference() {
                rsquare2(size, radius);
                x = size.x - wall * 2;
                y = size.y - wall * 2;
                rsquare2([x, y], radius);
            }
        } else {
            rsquare2(size, radius);
        }
}

module raspberry_pi() {
    pcb=1.6;
    w=85;
    h=56;
    difference() {
        color("#060")
        translate([0,0,-pcb])
            cube([h, w, 1.6]);
        
        // mounting holes
        translate([3.5, 3.5, 0])
            cylinder(h=10, r=2.5/2, center=true, $fn=180);
        translate([h-3.5, 3.5, 0])
            cylinder(h=10, r=2.5/2, center=true, $fn=180);
        translate([h-3.5, 3.5+58, 0])
            cylinder(h=10, r=2.5/2, center=true, $fn=180);
        translate([3.5, 3.5+58, 0])
            cylinder(h=10, r=2.5/2, center=true, $fn=180);
    }
    
    // USB-C
    translate([56-3, 3.5+7.7, 3.2/2])
        cube([7.35, 8.94 ,3.2], center=true);
    // HDMI-A-1
    translate([56-3, 3.5+7.7+14.8, 3/2])
        cube([7.5, 6.2, 3], center=true);
    // HDMI-A-2
    translate([56-3, 3.5+7.7+14.8+13.5, 3/2])
        cube([7.5, 6.2, 3], center=true);

    // Ethernet
    translate([56-45.75, 85-(21/2)+2, 13.5/2])
        cube([15, 21, 13.5], center=true);
    // USB 1
    translate([56-27, 85-(16/2)+2, 16/2])
        cube([13, 16, 16], center=true);
    // USB 2
    translate([56-9, 85-(16/2)+2, 16/2])
        cube([13, 16, 16], center=true);
}

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

module hexbolt(h, r, center) {
    difference() {
        cylinder(h=h,r=r, center=center, $fn=6);
        cylinder(h=h+0.1,r=2.5/2, center=center, $fn=45);
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
    
    // Corner mounts
    md = d-pcb;
    hoff = (h-68)/2;
    woff = (w-113)/2;
    translate([hoff, woff,d-md/2])
        hexbolt(h=md,r=3.2, center=true);
    translate([h-hoff, woff,d-md/2])
        hexbolt(h=md,r=3.2, center=true);
    translate([h-hoff, w-woff,d-md/2])
        hexbolt(h=md,r=3.2, center=true);
    translate([hoff, w-woff,d-md/2])
        hexbolt(h=md,r=3.2, center=true);
        
    // Pi mounts
    translate([76-4-12.5-49, 4+37.5,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);
    translate([76-4-12.5, 4+37.5,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);
    translate([76-4-12.5-49, 4+37.5+58,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);
    translate([76-4-12.5, 4+37.5+58,d-md/2])
        cylinder(h=md,r=3.2, center=true, $fn=6);

        
    // DSI connector
    color("#eee")
    translate([h/2-20.6/2, w-5, pcb])
        cube([20.6,3, 5.5]);
        
    // The touch flex sticks out a bit
    color("#09f")
    translate([-1.5,20,4])
        cube([3, 10, 8], center=true);
}

module mount_cs(thick=8, width=140, height=90) {
    inset=22.5;
    if($preview && show_modules) {
        translate([width/2, height/2, -inset])
            picam_cs();
    }
    translate([0,0,-thick])
        difference () {
        union() {
            cube([width, height, thick]);
            
            translate([width/2, height/2, (inset-thick)/2-(inset-thick)])
            rotate([0,0, 45])
                cylinder($fn=4, h=inset-thick, r1=30, r2=42, center=true);
        }
        
        // Lens hole
        translate([width/2, height/2, 2.5])
            cylinder(h=inset+thick+10, r=38/2, center=true, $fn=180);
            
        // Inset front
        translate([width/2, height/2, thick/2+0.01])
            cylinder(h=thick, r1=23, r2=32, center=true, $fn=180);
        
        // Sensor screw holes
        soff = (38/2)-4;
        translate([width/2-soff, height/2-soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);
        translate([width/2+soff, height/2-soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);
        translate([width/2-soff, height/2+soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);
        translate([width/2+soff, height/2+soff, -inset+thick-0.01])
            rotate([180, 0, 0])
            insert(2.5, 4.2, 5);

        
        // Hole for lens focus clamp
        translate([width/2,height/2+21,(-inset/2)-1])
            cube([12, 8, inset], center=true);
        }        
}

module waveshare_with_pi() {
    waveshare5inch();
    translate([63,103, 15])
    rotate([0,0, 180])
        raspberry_pi();
}