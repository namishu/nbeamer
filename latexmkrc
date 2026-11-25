use File::Basename qw(dirname);
use Cwd qw(abs_path);
my $root = dirname(abs_path($rc_files_read[-1]));
$ENV{TEXINPUTS} = "$root/tex:$root/docs:" . ($ENV{TEXINPUTS} // '');
$ENV{TTFONTS} = "$root/fonts:" . ($ENV{TTFONTS} // '');
$do_cd = 1;
my $bounds_checker = "$root/tools/check_bounds.py";
$xdvipdfmx .= qq{ && python3 "$bounds_checker" %D};
1;
