
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

render_bottom=true;

include<../lib/components.scad>;

module beam(length=100) {
    linear_extrude(length) {
        polygon([
            [0, bevel],
            [0, thick],
            [thick, thick],
            [thick, 0],
            [bevel, 0]
        ]);
    }
    translate([thick, thick-barw, 0])
        difference() {
            cube([bar, barw, length]);
            
            translate([screw_offset, -0.01, screw_offset])
            rotate([90, 0, 0])
                insert(2.5, 4, 5);
            
            translate([screw_offset, -0.01, length-screw_offset])
            rotate([90, 0, 0])
                insert(2.5, 4, 5);

        }
    translate([thick-barw, thick, 0])
        difference() {
            cube([barw, bar, length]);
            
            translate([-0.01, screw_offset, screw_offset])
            rotate([90, 0, -90])
                insert(2.5, 4, 5);
            
            translate([-0.01, screw_offset, length-screw_offset])
            rotate([90, 0, -90])
                insert(2.5, 4, 5);

        }
}

module triangle(short_edge, length) {
    linear_extrude(length) {
        polygon([
            [0, 0],
            [short_edge, 0],
            [0, short_edge]
        ]);
    }
}

module corner() {
    
    difference() {
        cube([thick, thick, thick]);
        
        translate([-0.5, -0.5, -0.5])
        triangle(bevel+1, thick+1);
        
        translate([thick+0.5, -0.5, -0.5])
        rotate([0, -90, 0])
            triangle(bevel+1, thick+1);
        
        translate([-0.5, thick+0.5, -0.5])
        rotate([90, 0, 0])
            triangle(bevel+1, thick+1);
        
        translate([thick, thick, thick]) {
        rotate([0, 54.8, 45])
        translate([0, 0, -12.05])
            cube([thick*2, thick, thick], center=true);
        }
    }
}

module frame_fb() {
    translate([0, 0, thick])
    beam(length=inner_height);
    
    translate([inner_width+thick, 0, 0])
    rotate([0, -90, 0])
    beam(length=inner_width);
    
    translate([width, 0, inner_height+thick])
    rotate([0, 180, 0])
    beam(length=inner_height);
    
    translate([thick, 0, height])
    rotate([0, 90, 0])
    beam(length=inner_width);

}

module frame() {
    frame_fb();
    
    translate([width, length, 0])
    rotate([0, 0, 180])
    frame_fb();
    
    translate([0, thick, 0])
    rotate([0, 180, 0])
    rotate([0, 90, 90])
    beam(length=inner_length);

    translate([width, thick, 0])
    rotate([0, 90, 0])
    rotate([0, 90, 90])
    beam(length=inner_length);

    translate([width, thick, height])
    rotate([0, 0, 0])
    rotate([0, 90, 90])
    beam(length=inner_length);
    
    translate([0, thick, height])
    rotate([0, 270, 0])
    rotate([0, 90, 90])
    beam(length=inner_length);

    corner();
    
    translate([width, 0, 0])
    rotate([0, 0, 90])
        corner();
    
    translate([0, 0, height])
    rotate([0, 90, 0])
        corner();

    translate([width, 0, height])
    rotate([0, 90, 90])
        corner();


    translate([0, length, 0])
    rotate([90, 0, 0])
        corner();

    translate([width, length, 0])
    rotate([90, 0, -90])
        corner();
    
    translate([0, length, height])
    rotate([90, 90, 0])
        corner();

    translate([width, length, height])
    rotate([-90, 90, 90])
        corner();
}

module panel(w,h) {
    difference() {
        cube([w, h, thick-barw]);
        
        translate([screw_offset, screw_offset, 0])
            screwhole(2.5, 4.5, 8, 2);
    }
}

difference() {
    frame();
    
    screw_offset=4.8;
    translate([screw_offset, screw_offset, height-thick-bar])
    union() {
        #insert(2.5, 4, 8);
        screwhole(2.5, 4.5, 8, 2);
    }
    translate([width-screw_offset, screw_offset, height-thick-bar])
    union() {
        #insert(2.5, 4, 8);
        screwhole(2.5, 4.5, 8, 2);
    }
    translate([screw_offset, length-screw_offset, height-thick-bar])
    union() {
        #insert(2.5, 4, 8);
        screwhole(2.5, 4.5, 8, 2);
    }
    translate([width-screw_offset, length-screw_offset, height-thick-bar])
    union() {
        #insert(2.5, 4, 8);
        screwhole(2.5, 4.5, 8, 2);
    }
    
    // Remove the bottom edge of the side panels to have a bit more clearance
    // for the LCD panel, but leave a little nub on the bottom to make the filler
    // panel not feel loose on the bottom
    nub_width=10;
    translate([0, thick*2, thick])
        cube([width, (length-thick*4)/2-(nub_width/2), thick]);
    translate([0, thick*2, thick+2])
        cube([width, (length-thick*4), thick]);
    translate([0,thick*2+(length-thick*4)/2+(nub_width/2), thick])
        cube([width, (length-thick*4)/2-(nub_width/2), thick]);


    if (render_bottom) {
        translate([-0.5, -0.5, height-thick-bar-0.01])
            cube([width+1, length+1, thick*2]);
    } else {
        translate([-0.5, -0.5, -0.01])
            cube([width+1, length+1, height-thick-bar]);
    }
}



// Make bottom solid
if(render_bottom) {
translate([thick, thick, 0])
difference() {
    cube([inner_width, inner_length, thick]);

    translate([inner_width/2, inner_length/2, 0])
        rotate([180, 0, 0])
            insert(0, 7, 8);
    
    translate([inner_width/2, inner_length/3, 0])
        rotate([180, 0, 0])
            insert(0, 7, 8);

    translate([inner_width/2, inner_length/3*2, 0])
        rotate([180, 0, 0])
            insert(0, 7, 8);

}
}

/*
translate([thick, thick-barw, thick])
rotate([90, 0, 0])
color("red")
panel(inner_width, inner_height);
*/