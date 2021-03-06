# -*- coding:utf-8 -*-

import re

commentsReg = re.compile(r'(.+?)?[ \t]*(?!\\)(%.+)')

addToHeaderReg = re.compile(r'\[header\]\n((?:(?:\t| {4}).*(?:\n|$))+)', re.IGNORECASE | re.MULTILINE)
metadataReg = re.compile(r'^\[(author|date|title): *(.+?)\](?:\n|$)', re.IGNORECASE | re.MULTILINE)
macroTagReg = re.compile(r'^\[(?:macro|define): *\\?(\w+?), *(.+?)\](?:\n|$)', re.MULTILINE|re.IGNORECASE)
includeTagReg = re.compile(r'^\[include: *([\w\d]+)((?:, ?[\w\d]+)*?)\](?:\n|$)', re.IGNORECASE | re.MULTILINE)
unincludeTagReg = re.compile(r'^\[(?:remove|uninclude): *([\w\d]+)\](?:\n|$)', re.IGNORECASE | re.MULTILINE)
figPathTagReg = re.compile(r'^\[figpath: *([\w\d/\.]+)\](?:\n|$)', re.IGNORECASE | re.MULTILINE)

theoremEnvReg = re.compile(r'\[(theorem|corollary|lemma|definition)(?:\:(.+?))*\]\n((?:\n*(?:\t| {4,}).+)+)', re.IGNORECASE | re.MULTILINE)
codeEnvReg = re.compile(r'(```|~~~~)([\w\d]+)*\n(.*?)\n\1([^\n]+)*', re.DOTALL)
mathEnvReg = re.compile(r'\$\$\$(\*)*(.*?)\$\$\$\*?\n?', re.DOTALL)

sectionReg = re.compile(r'^(#+)(\*)? *(.+)', re.MULTILINE)

# These 3 could probably be fused and then get context from \1,
#   but it's much safer to have reg #1 and #2 separated
emphasisReg = re.compile(r'(?<!\\)(\*|\/\/) *((?:(?!\1)(?:.|\\\n))+?) *(?<!\\)\1(?!\1)')
boldReg = re.compile(r'(?<!\\)(\*\*) *((?:(?!\1)(?:.|\\\n))+?) *(?<!\\)\1')
underlinedReg = re.compile(r'(?<!\\)(__) *((?:(?!\1)(?:.|\\\n))+?) *(?<!\\)\1')

crossedReg = re.compile(r'(~{2,})(.+)\1')
inlineCodeReg = re.compile(r'(?!``)`(.*?)`(?!``)')

listTabSize = 4
ulistReg = re.compile(r'^(?:([\*\-+.]) +.+(?:\n|$)(?:(?:\t| {4}).+\n*)*)+', re.MULTILINE)
olistReg = re.compile(r'^(?:\d+\. *.+(?:\n|$)(?:(?:\t| {4}).+\n*)*)+', re.MULTILINE)

hlineReg = re.compile(r'^-{3,}|\+{3,}|\*{3,}$', re.MULTILINE)

# Markdown table regex
prettyTableReg = re.compile(r'^(?:(?:\t| {4,})+([a-zA-Z0-9_\-:]+)\n)?\|\s*(.+)\n\s*\|(\s*[-:]+[-|\s:]*)\n((?:\s*\|.*(?:\n|$|\|))*)((?:(?:\t| {4}).+(?:\n|$))+)?', re.MULTILINE)
uglyTableReg = re.compile(r'()^ *(\S.*\|.*)\n *([-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))*)()', re.MULTILINE)
tableAlignReg = re.compile(r':?-{3,}:?')

# Blockquote
blockquoteReg = re.compile(r'(?:^ *> *[^\n]+(?:\n|$))+', re.MULTILINE)

# Center aligned eqs.
centerEq = re.compile(r'^(?:\t| {4,})+(\$.+\$)$', re.MULTILINE)

# Images
imageReg = re.compile(r'^[ \t]*!\[((?:.|(?:\n(?:\t| {4,})))+)?\]\((.+)\)[ \t]*\n?$', re.MULTILINE)

# Braces equation
bracesReg = re.compile(r'\[braces\]\n((?:(?:\t| {4}).*(?:\n|$))+)', re.IGNORECASE | re.MULTILINE)

def makeHeader(source):
    # Separate comments
    def splitComment(match):
        if match.group(1) is None:
            return match.group(2)
        return match.group(2) + '\n' + match.group(1)
    source = commentsReg.sub(splitComment, source)

    # Compiled tex string
    def addLine(*args):
        for line in args:
            addLine.compiled += line + '\n'
    addLine.compiled = ''

    addLine(r'% Start of header.')

    # Libs to include in the TeX file.
    # Include some useful predefined ones.
    includedLibs = {
        ('fontenc','T1'),
        ('inputenc','utf8'),
        ('amsmath',),
        ('amsthm',),
        ('amssymb',),
        ('lmodern',)
    }

    # TeXDown files are always articles.
    addLine('\\documentclass{article}')

    # Check for user defined do not include packages
    tags = unincludeTagReg.findall(source)
    for tag in tags:
        found = False
        for included in includedLibs:
            if included[0] == tag:
                includedLibs.remove(included)
                found = True
                break
        if not found:
            raise Exception('Could not remove package {}, because it is not included!'.format(tag))

    # Check for user defined included packages
    tags = includeTagReg.findall(source)
    for tag in tags:
        newLib = []
        newLib.append(tag[0])
        if tag[1] != '':
            newLib += map(lambda x: x.strip(), tag[1][1:].split(','))
        includedLibs.add(tuple(newLib))
    
    # If the code environment is used, include listings
    if codeEnvReg.search(source) or inlineCodeReg.search(source):
        includedLibs.add(('listings',))

    # If strikeout is used, include ulem
    if crossedReg.search(source):
        includedLibs.add(('ulem','normalem'))
    
    # If blockquote is used, include csquotes
    if blockquoteReg.search(source):
        includedLibs.add(('csquotes',))
    
    # If tables are used, include tabulary
    if prettyTableReg.search(source) or uglyTableReg.search(source):
        includedLibs.add(('tabulary',))
    
    # If images are used, include graphicx
    if imageReg.search(source):
        includedLibs.add(('graphicx',))
    
    # If braces are used, include empheq
    if (bracesReg.search(source)):
        includedLibs.add(('empheq',))

    # If minipages are used, include captionof
    if source.find('\\begin{minipage}'):
        includedLibs.add(('caption',))

    # Make library includes
    for lib in includedLibs:
        includeStr = r'\usepackage'
        if len(lib) > 1:
            includeStr += '['
            includeStr += ','.join(lib[1:])
            includeStr += ']'
        includeStr += '{{{}}}'.format(lib[0])

        addLine(includeStr)

    # Define macros/newcommand
    macros = macroTagReg.findall(source)
    if len(macros) > 0:
        addLine('')
        for macro in macros:
            # Find the highest argument number used;
            #   that's the ammount of args required.
            numberOfArgs = 0
            argNums = re.findall(r'(?<!\\)#(\d+?)', macro[1])
            if len(argNums) > 0:
                numberOfArgs = max(argNums)
            # Make macro
            addLine(r'\newcommand{{\{}}}[{}]{{{}}}'.format(macro[0], numberOfArgs, macro[1]))
    
    # Set gather to a more readable spacing
    addLine('')
    addLine(r'\setlength{\jot}{8pt}')

    # Define theorems
    theorems = theoremEnvReg.findall(source)
    if len(theorems) > 0:
        addLine('')
        theoremNumber = 0
        for theorem in theorems:
            newTheoremCommand = ''
            if theorem[1] != '':
                newTheoremCommand += r'\newtheorem*{{theorem{}}}'.format(theoremNumber)
                newTheoremCommand += r'{{{}}}'.format(theorem[1])
            else:
                newTheoremCommand += r'\newtheorem{{theorem{}}}'.format(theoremNumber)
                newTheoremCommand += r'{{{}}}'.format(theorem[0].lower().capitalize())
            addLine(newTheoremCommand)
            theoremNumber += 1

    # Look for title, author, date tags.
    #   LaTeX requires all or none.
    metadataTags = metadataReg.findall(source)
    if len(metadataTags) > 0:
        addLine('')
        title, author, date = '', '', ''
        for tag in metadataTags:
            if tag[0] == 'title':
                title = tag[1]
            elif tag[0] == 'author':
                author = tag[1]
            elif tag[0] == 'date':
                date = tag[1]
        addLine(r'\title{{{}}}'.format(title))
        addLine(r'\author{{{}}}'.format(author))
        addLine(r'\date{{{}}}'.format(date))
    
    # Add graphixpath, if any
    if imageReg.search(source) and figPathTagReg.search(source):
        addLine(r'\graphicspath{{{{{}}}}}'.format(figPathTagReg.search(source).group(1)))

    # Look and add any custom header contents
    headerContents = addToHeaderReg.findall(source)
    if len(headerContents) > 0:
        addLine('')
        addLine(r'% Start of custom header contents')
        for match in headerContents:
            addLine(match.strip())
        addLine(r'% End of custom header contents')
        addLine('')

    addLine(r'% End of header')
    addLine('')
    return addLine.compiled.strip()


def makeBody(source):
    # Valid LaTeX for body of document, in string form.
    def addLine(*args):
        for line in args:
            addLine.compiled += line + '\n'
    addLine.compiled = ''
    
    addLine(r'% Start of body.')
    addLine('')
    addLine(r'\begin{document}')
    addLine('')

    # If any metadata was specified, make title page.
    if metadataReg.search(source):
        addLine(r'\maketitle')
    
    # Separate comments
    def splitComment(match):
        if match.group(1) is None:
            return match.group(2)
        # Comment \n text
        return match.group(2) + '\n' + match.group(1)
    clearSource = commentsReg.sub(splitComment, source)

    # Remove metadata tags
    clearSource = metadataReg.sub('', clearSource)

    # Remove macro tags
    clearSource = macroTagReg.sub('', clearSource)

    # Remove uninclude tags
    clearSource = unincludeTagReg.sub('', clearSource)

    # Remove include tags
    clearSource = includeTagReg.sub('', clearSource)

    # Remove header tags
    clearSource = addToHeaderReg.sub('', clearSource)

    # Remove figpath tags
    clearSource = figPathTagReg.sub('', clearSource)

    # strip
    clearSource = clearSource.strip()

    # Replace all code envs. with lstlisting codes
    def makelstlisting(match):
        language = r'language={}'.format(match.group(2)) if match.group(2) is not None else ''
        caption = r'caption={}'.format(match.group(4)) if match.group(4) is not None else ''
        code = match.group(3)
        return r'''\begin{{lstlisting}}[{}]
{}
\end{{lstlisting}}'''.format(','.join([language,caption]), code)
    clearSource = codeEnvReg.sub(makelstlisting, clearSource)

    # Define function to know if we're inside code env.
    def inCodeEnv(pos):
        if clearSource.count(r'\begin{lstlisting}', 0, pos) > clearSource.count(r'\end{lstlisting}', 0, pos):
            return True
        return False
    
    # Define function to know if we're inside minipage env.
    def inMinipageEnv(pos):
        if clearSource.count(r'\begin{minipage}', 0, pos) > clearSource.count(r'\end{minipage}', 0, pos):
            return True
        return False

    # Define funciton to know if we're inside math env.
    def inMathEnv(pos):
        if len(re.findall(r'\\begin\{gather\*?\}', clearSource[0:pos])) > len(re.findall(r'\\end\{gather\*?\}', clearSource[0:pos])):
            return True
        return False

    # Make inline code
    clearSource = inlineCodeReg.sub(r'\\lstinline[columns=fixed]$\1$', clearSource)

    # Replace all $$$ envs with equation environments
    #   and $$$* with equation* environements
    def returnEqEnv(match):
        return '\\begin{{gather{star}}}\n{}\n\\end{{gather{star}}}\n'.format(
            '\\\\\n'.join(
                map(lambda eq: ' '.join(eq.split('\n')), match.group(2).split('\n\n'))
            ).strip(),
            star = '*' if match.group(1) is not None else ''
        )
    clearSource = mathEnvReg.sub(returnEqEnv, clearSource)

    # Replace all theorem tags with theorem envs.
    # Matching order from leftmost assures correct theorem name order
    #   but I'd enjoy something cleaner, while still detatching
    #   makeHead from makeBody
    global theoremNumber
    theoremNumber = -1
    def replaceWithName(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        global theoremNumber
        theoremNumber += 1
        return '\\begin{{theorem{}}}\n{}\n\\end{{theorem{}}}'.format(theoremNumber,match.group(3), theoremNumber)
    clearSource = theoremEnvReg.sub(replaceWithName, clearSource)

    # Make emphasis, bolds, underline and crossed out
    def makeFormat(command):
        def subFormat(match):
            if inCodeEnv(match.end(0)) or inMathEnv(match.end(0)):
               return match.group(0) 
            return '\\{}{{{}}}'.format(command, match.group(2).replace('\\\n', '\n'))
        return subFormat
    clearSource = boldReg.sub(makeFormat('textbf'), clearSource)
    clearSource = emphasisReg.sub(makeFormat('emph'), clearSource)
    clearSource = underlinedReg.sub(makeFormat('underline'), clearSource)
    clearSource = crossedReg.sub(makeFormat('sout'), clearSource)

    # Make brace environments
    def makeBraces(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        
        if match.group(1) is None:
            return ''

        result = r'\begin{empheq}[left=\empheqlbrace\,]{align}'
        result += '\n'

        equations = []
        for equation in match.group(1).split('\n'):
            if equation == '':
                continue
            equations.append( '& {}'.format(equation.strip()))
        result += '\\\\\n'.join(equations)
        
        result += '\n'
        result += '\\end{empheq}\n'

        return result

    clearSource = bracesReg.sub(makeBraces, clearSource)

    # Make all (sub)*sections
    def makeSection(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        sectionDepth = match.group(1).count('#')
        depthKey = {
            1:'section',
            2:'subsection',
            3:'subsubsection',
            4:'paragraph',
            5:'subparagraph'
        }
        sectionType = depthKey.get(sectionDepth, 'subparagraph')
        return r'\{}{}{{{}}}'.format(sectionType, '' if match.group(2) is None else '*', match.group(3))
    clearSource = sectionReg.sub(makeSection, clearSource)

    # Make lists
    def makeList(group, elemRegex):
        def makeGroupList(match):
            if inCodeEnv(match.end(0)) or inMathEnv(match.end(0)):
                return match.group(0)
            output = ''
            curDepth = -1
            for line in filter(None, match.group(0).split('\n')):
                depth = 0
                contentStart = 0
                for char in line:
                    if char not in (' ','\t'):
                        break
                    if char == ' ':
                        depth += 1
                    elif char == '\t':
                        depth += listTabSize
                    contentStart += 1
                depth/=listTabSize

                while depth > curDepth:
                    output += '\\begin{{{}}}\n'.format(group)
                    curDepth = depth
                while depth < curDepth:
                    output += '\\end{{{}}}\n'.format(group)
                    curDepth -= 1
                
                output += '\\item {}\n'.format(re.search(elemRegex, line).group(1))
            while curDepth > -1:
                output += '\\end{{{}}}\n'.format(group)
                curDepth -= 1
            return output
        return makeGroupList

    clearSource = ulistReg.sub(makeList('itemize', r'(?:[\*\-+.]?[ \t]*)?(.+)'), clearSource)
    clearSource = olistReg.sub(makeList('enumerate', r'(?:(?:\d+\.?)|[ \t])* *(.+)'), clearSource)

    # Make hotizontal line breaks
    clearSource = hlineReg.sub(r'\\vspace{0.2mm}\\rule{\\textwidth}{0.4pt}\n\\vspace{0.2mm}', clearSource)

    # Make tables
    def makeTables(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        out = ''

        if not inMinipageEnv(match.end(0)):
            out += '\\begin{table}[hbpt]\n\\noindent\\makebox[\\textwidth]{\n'

        out += r'''\centering
\setlength{\tabcolsep}{10pt}
\renewcommand{\arraystretch}{1.5}'''

        if inMinipageEnv(match.end(0)):
            out += '\n\\begin{tabulary}{\\textwidth}'
        else:
            out += '\n\\begin{tabulary}{\\paperwidth}'

        # Get alignments
        alignLine = match.group(3)
        alignmentsWithSeparator = re.search(r'\s*\|?(.+)\|?\s*', alignLine).group(1)
        alignments = {}
        columns = alignmentsWithSeparator.split('|')
        position = 0
        for align in columns:
            align = align.strip()
            colonCount = align.count(':')
            if colonCount == 1 and align.find(':') * 1.0 / len(align) > 0.5:
                alignments[position] = 'R'
            elif colonCount == 2:
                alignments[position] = 'C'
            position += 1
        
        # Create tags
        out += '{ |' + '|'.join([alignments.get(i, 'L') for i in range(len(columns))]) + '| }'
        out += '\n\\hline\n'
        
        # Create table "header"
        header = match.group(2)
        if header[0] == '|':
            header = header[1:]
        if header[-1] == '|':
            header = header[:-1]
        elems = header.split('|')
        elems = map(lambda x: x.strip(), elems)
        out += ' & '.join(elems) + ' \\\\ \\hline \\hline\n'

        # Create actual table (skipping alignment lines)
        for line in match.group(4).splitlines():
            if line == '':
                continue
            line = line.strip()
            if line[0] == '|':
                line = line[1:]
            if line[-1] == '|':
                line = line[:-1]
            elems = line.split('|')
            elems = map(lambda x: x.strip(), elems)
            out += ' & '.join(elems) + ' \\\\ \\hline\n'
        
        # Find caption if available
        caption = ''
        if match.group(5) is not None and match.group(5) != '':
            caption = '\n\\caption{{{}}}'.format(('\n' + match.group(5)))

        # Find label if available
        label = '\n'
        if match.group(1) is None or match.group(1) == '':
            label += '\\label{{{}}}'.format('table' + str(makeTables.tableNumber))
        else:
            label += '\\label{{{}}}'.format(match.group(1))

        out += '\\end{tabulary}'

        if not inMinipageEnv(match.end(0)):
            out += '\n}}{}{}\n\\end{{table}}\n'.format(caption, label)
        makeTables.tableNumber += 1
        return out
    
    makeTables.tableNumber = 1

    clearSource = prettyTableReg.sub(makeTables, clearSource)
    clearSource = uglyTableReg.sub(makeTables, clearSource)
    
    # Make blockquotes
    def makeBq(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        out = '\\begin{displayquote}\n'
        out += '\n\n'.join(map(lambda match: match[1], re.findall(r'( *> *)(.+)', match.group(0))))
        out += '\n\\end{displayquote}\n'
        return out
    clearSource = blockquoteReg.sub(makeBq, clearSource)

    # Make images
    def makeImgs(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        if match.group(1) is not None:
            caption = '\n\t\t'.join(map(lambda x: x.strip(), match.group(1).split('\n')))
        out = ''
        
        if inMinipageEnv(match.end(0)):
            out += '\t\\centering\n\t'
        else:
            out += '\\begin{figure}[hbtp]\n'
        
        out += '\\includegraphics[width=\\textwidth,keepaspectratio]{{{}}}\n'.format(match.group(2))
        
        if match.group(1) is not None:
            if inMinipageEnv(match.end(0)):
                out += '\t\\captionof{{figure}}{{{}}}\n'.format(caption)
            else:
                out += '\t\\caption{{{}}}\n'.format(caption)
        

        out += '\t\\label{{{}}}\n'.format(match.group(2))

        if not inMinipageEnv(match.end(0)):
            out += '\\end{figure}\n'
        return out
    clearSource = imageReg.sub(makeImgs, clearSource)

    # Make align shortcuts
    def makeAlign(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        return '\\begin{{center}}\n{}\n\\end{{center}}'.format(match.group(1))
    clearSource = centerEq.sub(makeAlign, clearSource)

    # Escape double linebreaks as vspaces
    def makeVspaces(match):
        if inCodeEnv(match.end(0)):
            return match.group(0)
        return '\n\\vspace{5mm}\n\n'
    clearSource = re.sub(r'^\n\n', makeVspaces, clearSource, 0, re.MULTILINE)

    # Add handled text
    addLine(clearSource)

    addLine(r'\end{document}')
    addLine(r'% End of body.')

    return addLine.compiled.strip()