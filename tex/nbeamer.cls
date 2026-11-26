\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{nbeamer}[2026/11/25 v0.1.0 Grid-based bilingual slides]
% Font selection happens before the document preamble.
\def\nbeamer@fontset{auto}
\DeclareOption{fontset=auto}{\def\nbeamer@fontset{auto}}
\DeclareOption{fontset=fandol}{\def\nbeamer@fontset{fandol}}
\DeclareOption{fontset=custom}{\def\nbeamer@fontset{custom}}
\DeclareOption*{\ClassError{nbeamer}{Unsupported class option '\CurrentOption'}{Choose fontset=auto, fandol, or custom.}}
\ProcessOptions\relax
\LoadClass[aspectratio=169,t,onlytextwidth]{beamer}
\RequirePackage{iftex}
\RequireXeTeX
\RequirePackage{xeCJK}
\RequirePackage{xeCJKfntef}
\RequirePackage{tikz}
\RequirePackage{booktabs}
\RequirePackage{ragged2e}
\input{nbeamer-fonts.def}

% Beamer typography and color roles.
\setbeamercolor{subtitle}{fg=black!65}
\setbeamercolor*{date}{fg=black!50}
\setbeamercolor{normal text}{fg=black,bg=white}
\setbeamercolor{structure}{fg=black}
\definecolor{nbeamerMute}{HTML}{686868}
\definecolor{nbeamerEmphasis}{HTML}{245B94}
\definecolor{nbeamerAlert}{HTML}{A33939}
\DeclareRobustCommand{\nbmute}[1]{\textcolor{nbeamerMute}{#1}}
\DeclareRobustCommand{\nbemph}[1]{\textcolor{nbeamerEmphasis}{#1}}
\setbeamercolor{alerted text}{fg=nbeamerAlert}
\setbeamercolor{example text}{fg=black}
\setbeamercolor{button}{fg=white,bg=black}
\setbeamercolor{button border}{fg=black}
\setbeamercolor{bibliography entry location}{fg=black}
\setbeamercolor{bibliography entry note}{fg=black}
\setbeamercolor{note page}{bg=white,fg=black}
\setbeamercolor{note title}{bg=white,fg=black}
\setbeamertemplate{section in toc shaded}[default][100]
\setbeamertemplate{subsection in toc shaded}[default][100]
\hypersetup{hidelinks}
\renewcommand<>{\emph}[1]{\alt#2{{\def\ULthickness{.55pt}\CJKunderline{#1}}}{#1}}
\pdfstringdefDisableCommands{%
  \let\emph\@firstofone
  \let\nbmute\@firstofone
  \let\nbemph\@firstofone}
\setbeamerfont{alerted text}{series=\bfseries}
\setbeamerfont{structure}{series=\bfseries}
\setbeamerfont{section in toc}{size=\large,series=\mdseries}
\setbeamerfont{title}{size=\LARGE,series=\bfseries}
\setbeamerfont{frametitle}{size=\Large,series=\bfseries}
\setbeamerfont{subtitle}{series=\mdseries}
\setbeamerfont{author}{series=\bfseries}
\renewcommand<>{\framesubtitle}[1]{%
  \only#2{\ifblank{#1}{}{\ClassWarning{nbeamer}{Frame subtitle ignored; use frametitle only}}}}
\setbeamercolor*{institute}{parent=subtitle}
\setbeamerfont{institute}{size=\footnotesize}
\setbeamerfont{date}{size=\scriptsize}
\setbeamerfont{caption}{size=\small}
\setbeamerfont{block title}{size=\normalsize,series=\bfseries}
% A 16:9 canvas contains 32 by 18 square layout units.
\newlength{\nbeamer@gridunit}
\setlength{\nbeamer@gridunit}{\dimexpr\paperwidth/32\relax}
\newcommand*{\nbgrid}{\dimexpr\nbeamer@gridunit\relax}
\newlength{\nbeamer@firstbaseline}
\setlength{\nbeamer@firstbaseline}{.75\nbeamer@gridunit}
\newlength{\nbeamer@baselinedepth}
\setlength{\nbeamer@baselinedepth}{\dimexpr\nbeamer@gridunit-\nbeamer@firstbaseline\relax}
% Shared internal layout dimensions.
\newlength{\nbeamer@defaultmargin}
\setlength{\nbeamer@defaultmargin}{2\nbeamer@gridunit}
\newlength{\nbeamer@bodybottom}
\setlength{\nbeamer@bodybottom}{2\nbeamer@gridunit}
\newlength{\nbeamer@untitledtop}
\setlength{\nbeamer@untitledtop}{2\nbeamer@gridunit}
\newlength{\nbeamer@titledtop}
\setlength{\nbeamer@titledtop}{4\nbeamer@gridunit}
% Capture the final page geometry before a column or minipage narrows textwidth.
\newlength{\nbeamer@bodyleft}
\newlength{\nbeamer@layoutwidth}
\AtBeginDocument{%
  \setlength{\nbeamer@bodyleft}{\dimexpr 1in+\hoffset+\oddsidemargin\relax}%
  \setlength{\nbeamer@layoutwidth}{\textwidth}}
\newcommand{\nbeamer@bodyright}{\dimexpr\nbeamer@bodyleft+\nbeamer@layoutwidth\relax}
\newcommand{\nbeamer@specialwidth}{\dimexpr\nbeamer@layoutwidth-2\nbeamer@gridunit\relax}
\newcommand{\nbeamer@bodytop}{%
  \nbeamer@ifuntitled{\nbeamer@untitledtop}{\nbeamer@titledtop}}
\newcommand{\nbeamer@bodyheight}{\dimexpr\paperheight-\nbeamer@bodybottom-\nbeamer@bodytop\relax}
\setbeamersize{text margin left=\nbeamer@defaultmargin,text margin right=\nbeamer@defaultmargin,
  sidebar width left=0pt,sidebar width right=0pt}
\setbeamerfont{table body}{size=\small}
\newcommand{\nbeamer@gridbaseline}{\fontsize{\f@size}{\nbeamer@gridunit}\selectfont}
% Use a grid baseline and one blank grid row between body paragraphs.
\AtBeginEnvironment{beamer@framepauses}{%
  \nbeamer@gridbaseline
  \setlength{\parskip}{\nbeamer@gridunit}}
% A top container starts at a known edge, with its first text baseline
% three quarters of a row below it. Nested lists and verbatim own their spacing.
\newif\ifnbeamer@firstparagraph
\newcommand{\nbeamer@startbody}{%
  \prevdepth=\nbeamer@baselinedepth
  \parskip=\nbeamer@gridunit
  \nbeamer@firstparagraphtrue
  \@setminipage}
\AddToHook{para/begin}{\ifnbeamer@firstparagraph\global\nbeamer@firstparagraphfalse\fi}
% Spacing and geometry consumed by the optional packages.
\newcommand*{\nbeamer@beforeblockskip}{\ifnbeamer@firstparagraph 0pt\else\nbgrid\fi}
\newcommand{\nbeamer@floatspacing}{%
  \par\ifnbeamer@firstparagraph\else\vskip\nbeamer@gridunit\fi
  \nointerlineskip
  \setlength{\topsep}{0pt}\setlength{\partopsep}{0pt}\setlength{\parskip}{0pt}}
\AtBeginEnvironment{table}{\nbeamer@floatspacing}
\AtBeginEnvironment{figure}{\nbeamer@floatspacing}
\newcommand{\nbeamer@tablefont}{%
  \usebeamerfont{table body}\nbeamer@gridbaseline
  \setlength{\tabcolsep}{.5\nbeamer@gridunit}%
  \setbox\strutbox=\hbox{\vrule width 0pt height \nbeamer@firstbaseline depth \nbeamer@baselinedepth}}
\AtBeginEnvironment{tabular}{\nbeamer@tablefont}
\AtBeginEnvironment{tabular*}{\nbeamer@tablefont}
\setlength{\abovecaptionskip}{\nbeamer@gridunit}
\setlength{\belowcaptionskip}{0pt}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{headline}{}
% Beamer adds 4pt to the measured footline height.
\setbeamertemplate{footline}{\rule{0pt}{\dimexpr\nbeamer@bodybottom-4pt\relax}}
\setbeamertemplate{sidebar left}{}
\setbeamertemplate{sidebar right}{}
% Beamer reads frame options before entering the slide group.
\newif\ifnbeamer@grid
\newif\ifnbeamer@boxes
\pgfkeys{/nbeamer/debug/.is family,
  /nbeamer/debug/grid/.is if=nbeamer@grid,
  /nbeamer/debug/boxes/.is if=nbeamer@boxes}
\newif\ifnbeamer@defaultgrid
\newif\ifnbeamer@defaultboxes
\pgfkeys{/nbeamer/defaults/.is family,
  /nbeamer/defaults/grid/.is if=nbeamer@defaultgrid,
  /nbeamer/defaults/boxes/.is if=nbeamer@defaultboxes}
\newcommand*{\nbsetup}[1]{\pgfkeys{/nbeamer/defaults/.cd,#1}}
\define@key{beamerframe}{nbeamer}{\pgfkeys{/nbeamer/debug/.cd,#1}}
\setbeamertemplate{background}{%
  \ifnbeamer@grid
    \begin{tikzpicture}
      \clip (0,0) rectangle (\paperwidth,\paperheight);
      \draw[black!12,line width=.2pt,step=\nbeamer@gridunit]
        (0,0) grid (\paperwidth,\paperheight);
    \end{tikzpicture}%
  \fi}
\tikzset{nbeamer page/.style={shift={(current page.north west)},
  xshift=\nbeamer@bodyleft,x=\nbeamer@gridunit,y=-\nbeamer@gridunit},
  nbeamer special page/.style={nbeamer page,xshift=\nbeamer@gridunit},
  nbeamer region/.style={draw=black!45,line width=.4pt}}

% Reserve the top margin after Beamer has collected the frame body and title.
\newif\ifnbeamer@specialpage
% A full-page layout supplies its own boxes in place of the default body.
\newcommand{\nbeamer@beginspecialpage}{\global\nbeamer@specialpagetrue}
% Select the body rectangle for the current slide.
% XeTeX's xdvipdfmx page stream uses the DVI origin: one inch from the
% upper left. PDF rectangle coordinates grow upwards and are in bp.
\newcommand{\nbeamer@drawbodybox}{%
  \draw[nbeamer region] ([xshift=\nbeamer@bodyleft,yshift=-\nbeamer@bodytop]current page.north west)
    rectangle ([xshift=\nbeamer@bodyright,yshift=\nbeamer@bodybottom]current page.south west);}
\ExplSyntaxOn
\cs_new_eq:NN \nbeamer@bp \dim_to_decimal_in_bp:n
\ExplSyntaxOff
\newcommand{\nbeamer@clipbody}{%
  \pdfstringdef\nbeamer@pdftitle{\nbeamer@shortframetitle}%
  \special{pdf:put @thispage << /NBeamerTitle (\nbeamer@pdftitle)
    /NBeamerFrame \the\c@framenumber\space
    /NBeamerBody [\nbeamer@bp{\nbeamer@bodyleft} \nbeamer@bp{\nbeamer@bodybottom}
    \nbeamer@bp{\nbeamer@bodyright} \nbeamer@bp{\paperheight-\nbeamer@bodytop}] >>}%
  \special{pdf:code q /NBeamerBody BMC
    \nbeamer@bp{\nbeamer@bodyleft-1in} \nbeamer@bp{\nbeamer@bodybottom-\paperheight+1in}
    \nbeamer@bp{\nbeamer@layoutwidth}
    \nbeamer@bp{\nbeamer@bodyheight} re W n}%
}
\setbeamertemplate{frametitle}{%
  \vskip\nbeamer@gridunit
  \nointerlineskip\vbox to \dimexpr\nbeamer@titledtop-2\nbeamer@gridunit\relax{\vfil
    \raggedright\noindent\nbeamer@singleline{Frame title}{\insertframetitle}\par
    \vfil}%
  \vskip\nbeamer@gridunit
  \ifnbeamer@boxes
    \nointerlineskip\hbox{\begin{tikzpicture}[remember picture,overlay]
      \begin{scope}[shift={(current page.north west)},x=\nbeamer@gridunit,y=-\nbeamer@gridunit]
        \draw[nbeamer region] (\nbeamer@bodyleft,-\nbeamer@gridunit) rectangle (\dimexpr\nbeamer@bodyright\relax,\dimexpr\nbeamer@gridunit-\nbeamer@titledtop\relax);
      \end{scope}
      \nbeamer@drawbodybox
    \end{tikzpicture}}%
  \fi}
% Typeset once so measurement includes the active font and formatted text.
\newsavebox{\nbeamer@fieldbox}
\NewDocumentCommand{\nbeamer@fieldbreak}{s o}{\unskip\space\ignorespaces}
\newcommand{\nbeamer@singleline}[2]{%
  \begingroup
  \sbox{\nbeamer@fieldbox}{\let\\\nbeamer@fieldbreak
    \let\newline\nbeamer@fieldbreak#2}%
  \ifdim\wd\nbeamer@fieldbox>\linewidth
    \ClassWarning{nbeamer}{#1 exceeds its line width; truncated}%
    \begin{pgfpicture}
      \pgfsetbaseline{0pt}%
      \pgfpathrectanglecorners
        {\pgfpoint{0pt}{-\dp\nbeamer@fieldbox}}
        {\pgfpoint{\linewidth}{\ht\nbeamer@fieldbox}}%
      \pgfusepath{use as bounding box,clip}%
      \pgftext[left,base]{\usebox{\nbeamer@fieldbox}}%
    \end{pgfpicture}%
  \else
    \usebox{\nbeamer@fieldbox}%
  \fi
  \endgroup}
\input{nbeamer-pages.def}
% Format the standard date command; the cover date remains opt-in.
\renewcommand*{\today}{\number\year-\ifnum\month<10 0\fi\number\month-\ifnum\day<10 0\fi\number\day}
\date{}
\setbeamertemplate{caption}{\insertcaption}
\setlength{\leftmargini}{2\nbeamer@gridunit}
\setlength{\leftmarginii}{\nbeamer@gridunit}
\setlength{\leftmarginiii}{\nbeamer@gridunit}
% Other list-based environments retain their normal first-level separation.
\newcommand{\nbeamer@firstlistsep}{\nbeamer@gridunit}
\newcommand{\nbeamer@listspacing}[1]{%
  \setlength{\itemsep}{\nbeamer@gridunit}%
  \setlength{\topsep}{#1}%
  \setlength{\parsep}{0pt}\setlength{\partopsep}{0pt}}
\appto\@listi{\nbeamer@listspacing{\nbeamer@firstlistsep}}
\let\@listI\@listi
\appto\@listii{\nbeamer@listspacing{\nbeamer@gridunit}}
\appto\@listiii{\nbeamer@listspacing{\nbeamer@gridunit}}
\newlength{\nbeamer@itemcenter}
\newcommand{\nbeamer@itembaseline}{%
  \nbeamer@gridbaseline
  \setbox\@tempboxa=\hbox{中}%
  \nbeamer@itemcenter=\dimexpr(\ht\@tempboxa-\dp\@tempboxa)/2\relax}
\addtobeamertemplate{itemize/enumerate body begin}{}{\nbeamer@itembaseline}
\addtobeamertemplate{itemize/enumerate subbody begin}{}{\nbeamer@itembaseline}
\addtobeamertemplate{itemize/enumerate subsubbody begin}{}{\nbeamer@itembaseline}
\newcommand{\nbeamer@listindent}{%
  \def\nbeamer@firstlistsep{0pt}%
  \setlength{\leftmargini}{\nbeamer@gridunit}}
\AtBeginEnvironment{enumerate}{%
  \nbeamer@listindent
  \ifnum\@listdepth=1\relax
    \setlength{\leftmarginii}{2\nbeamer@gridunit}%
  \fi
  \setlength{\labelsep}{0pt}}
\AtBeginEnvironment{itemize}{%
  \nbeamer@listindent
  % Beamer right-aligns each label against the text indent minus labelsep.
  \ifnum\@itemdepth=0
    \settowidth{\labelsep}{\usebeamertemplate{itemize item}}%
  \else
    \settowidth{\labelsep}{\usebeamertemplate{itemize subitem}}%
  \fi
  \setlength{\labelsep}{\dimexpr(\nbeamer@gridunit-\labelsep)/2\relax}%
  \ifnum\@itemdepth>1\relax
    \ClassError{nbeamer}{Itemize supports only two levels}{Move this item into the second level.}%
  \fi}
\setbeamertemplate{itemize item}{%
  \begin{tikzpicture}[baseline=-\nbeamer@itemcenter,line cap=round]
    \draw[black!75,line width=.38pt,rounded corners=.42pt]
      (0,0) -- (0,-2.25pt) -- (4pt,0) -- (0,2.25pt) -- cycle;
    \draw[black,line width=.58pt] (0,-1.83pt) -- (0,1.83pt);
  \end{tikzpicture}}
\setbeamertemplate{itemize subitem}{%
  \tikz[baseline=-\nbeamer@itemcenter]\draw[black!75,line width=.38pt] (0,0) circle[radius=1.35pt];}
\setbeamertemplate{enumerate item}{\insertenumlabel.}
% Share the default typography while preserving each environment's templates.
\newcommand{\nbeamer@blockbegin}[1]{%
  \par\setlength{\parskip}{\nbeamer@gridunit}%
  \ifx\insertblocktitle\@empty\else
    \sbox{\nbeamer@fieldbox}{{\usebeamerfont{#1}\insertblocktitle\@addpunct{.}}}%
    \noindent\usebox{\nbeamer@fieldbox}\nobreak\hspace{\nbeamer@gridunit}%
  \fi\ignorespaces}
\newcommand{\nbeamer@blockend}{\par}
\setbeamerfont*{block title alerted}{parent=block title}
\setbeamerfont*{block title example}{parent=block title}
\setbeamertemplate{block begin}{\nbeamer@blockbegin{block title}}
\setbeamertemplate{block alerted begin}{\nbeamer@blockbegin{block title alerted}}
\setbeamertemplate{block example begin}{\nbeamer@blockbegin{block title example}}
\setbeamertemplate{block end}{\nbeamer@blockend}
\setbeamertemplate{block alerted end}{\nbeamer@blockend}
\setbeamertemplate{block example end}{\nbeamer@blockend}
% Use the body baseline for wrapped lines and one blank row between paragraphs.
\addtobeamertemplate{proof begin}{}{\setlength{\parskip}{\nbeamer@gridunit}\ignorespaces}
% The proof line's baseline is a quarter grid above the lower edge.
\setbeamertemplate{qed symbol}{%
  \begingroup
  \setlength{\fboxsep}{0pt}%
  \raisebox{-\nbeamer@baselinedepth}{\fbox{\rule{0pt}{.6em}\rule{.6em}{0pt}}}%
  \endgroup}

\input{nbeamer-compat.def}
\endinput
