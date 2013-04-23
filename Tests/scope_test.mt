! Small scope test 
let
	var x: Integer;
	const c ~ 7; 
in
	begin
		x := 1;
		let
			var x: Integer; 
		in
			begin
				x := c;
				putint(x); 
			end
            putint(x); 
    end
