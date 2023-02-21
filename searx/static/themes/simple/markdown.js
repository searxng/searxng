// Markdown.Converter.js 
var Markdown;if(typeof exports==="object"&&typeof require==="function"){Markdown=exports}else{Markdown={}}(function(){function identity(x){return x}function returnFalse(x){return false}function HookCollection(){}HookCollection.prototype={chain:function(hookname,func){var original=this[hookname];if(!original){throw new Error("unknown hook "+hookname)}if(original===identity){this[hookname]=func}else{this[hookname]=function(text){var args=Array.prototype.slice.call(arguments,0);args[0]=original.apply(null,args);return func.apply(null,args)}}},set:function(hookname,func){if(!this[hookname]){throw new Error("unknown hook "+hookname)}this[hookname]=func},addNoop:function(hookname){this[hookname]=identity},addFalse:function(hookname){this[hookname]=returnFalse}};Markdown.HookCollection=HookCollection;function SaveHash(){}SaveHash.prototype={set:function(key,value){this["s_"+key]=value},get:function(key){return this["s_"+key]}};Markdown.Converter=function(){var options={};this.setOptions=function(optionsParam){options=optionsParam};var pluginHooks=this.hooks=new HookCollection();pluginHooks.addNoop("plainLinkText");pluginHooks.addNoop("preConversion");pluginHooks.addNoop("postNormalization");pluginHooks.addNoop("preBlockGamut");pluginHooks.addNoop("postBlockGamut");pluginHooks.addNoop("preSpanGamut");pluginHooks.addNoop("postSpanGamut");pluginHooks.addNoop("postConversion");var g_urls;var g_titles;var g_html_blocks;var g_list_level;this.makeHtml=function(text){if(g_urls){throw new Error("Recursive call to converter.makeHtml")}g_urls=new SaveHash();g_titles=new SaveHash();g_html_blocks=[];g_list_level=0;text=pluginHooks.preConversion(text);text=text.replace(/~/g,"~T");text=text.replace(/\$/g,"~D");text=text.replace(/\r\n/g,"\n");text=text.replace(/\r/g,"\n");text="\n\n"+text+"\n\n";text=_Detab(text);text=text.replace(/^[ \t]+$/mg,"");text=pluginHooks.postNormalization(text);text=_HashHTMLBlocks(text);text=_StripLinkDefinitions(text);text=_RunBlockGamut(text);text=_UnescapeSpecialChars(text);text=text.replace(/~D/g,"$$");text=text.replace(/~T/g,"~");text=pluginHooks.postConversion(text);g_html_blocks=g_titles=g_urls=null;return text};function _StripLinkDefinitions(text){text=text.replace(/^[ ]{0,3}\[(.+)\]:[ \t]*\n?[ \t]*<?(\S+?)>?(?=\s|$)[ \t]*\n?[ \t]*((\n*)["(](.+?)[")][ \t]*)?(?:\n+)/gm,function(wholeMatch,m1,m2,m3,m4,m5){m1=m1.toLowerCase();g_urls.set(m1,_EncodeAmpsAndAngles(m2));if(m4){return m3}else{if(m5){g_titles.set(m1,m5.replace(/"/g,"&quot;"))}}return""});return text}function _HashHTMLBlocks(text){var block_tags_a="p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|ins|del";var block_tags_b="p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math";text=text.replace(/^(<(p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math|ins|del)\b[^\r]*?\n<\/\2>[ \t]*(?=\n+))/gm,hashElement);text=text.replace(/^(<(p|div|h[1-6]|blockquote|pre|table|dl|ol|ul|script|noscript|form|fieldset|iframe|math)\b[^\r]*?<\/\2>[ \t]*(?=\n+)\n)/gm,hashElement);text=text.replace(/\n[ ]{0,3}((<(hr)\b([^<>])*?\/?>)[ \t]*(?=\n{2,}))/g,hashElement);text=text.replace(/\n\n[ ]{0,3}(<!(--(?:|(?:[^>-]|-[^>])(?:[^-]|-[^-])*)--)>[ \t]*(?=\n{2,}))/g,hashElement);text=text.replace(/(?:\n\n)([ ]{0,3}(?:<([?%])[^\r]*?\2>)[ \t]*(?=\n{2,}))/g,hashElement);return text}function hashElement(wholeMatch,m1){var blockText=m1;blockText=blockText.replace(/^\n+/,"");blockText=blockText.replace(/\n+$/g,"");blockText="\n\n~K"+(g_html_blocks.push(blockText)-1)+"K\n\n";return blockText}var blockGamutHookCallback=function(t){return _RunBlockGamut(t)};function _RunBlockGamut(text,doNotUnhash){text=pluginHooks.preBlockGamut(text,blockGamutHookCallback);text=_DoHeaders(text);var replacement="<hr />\n";text=text.replace(/^[ ]{0,2}([ ]?\*[ ]?){3,}[ \t]*$/gm,replacement);text=text.replace(/^[ ]{0,2}([ ]?-[ ]?){3,}[ \t]*$/gm,replacement);text=text.replace(/^[ ]{0,2}([ ]?_[ ]?){3,}[ \t]*$/gm,replacement);text=_DoLists(text);text=_DoCodeBlocks(text);text=_DoBlockQuotes(text);text=pluginHooks.postBlockGamut(text,blockGamutHookCallback);text=_HashHTMLBlocks(text);text=_FormParagraphs(text,doNotUnhash);return text}function _RunSpanGamut(text){text=pluginHooks.preSpanGamut(text);text=_DoCodeSpans(text);text=_EscapeSpecialCharsWithinTagAttributes(text);text=_EncodeBackslashEscapes(text);text=_DoImages(text);text=_DoAnchors(text);text=_DoAutoLinks(text);text=text.replace(/~P/g,"://");text=_EncodeAmpsAndAngles(text);text=options._DoItalicsAndBold?options._DoItalicsAndBold(text):_DoItalicsAndBold(text);text=text.replace(/  +\n/g," <br>\n");text=pluginHooks.postSpanGamut(text);return text}function _EscapeSpecialCharsWithinTagAttributes(text){var regex=/(<[a-z\/!$]("[^"]*"|'[^']*'|[^'">])*>|<!(--(?:|(?:[^>-]|-[^>])(?:[^-]|-[^-])*)--)>)/gi;text=text.replace(regex,function(wholeMatch){var tag=wholeMatch.replace(/(.)<\/?code>(?=.)/g,"$1`");tag=escapeCharacters(tag,wholeMatch.charAt(1)=="!"?"\\`*_/":"\\`*_");
return tag});return text}function _DoAnchors(text){text=text.replace(/(\[((?:\[[^\]]*\]|[^\[\]])*)\][ ]?(?:\n[ ]*)?\[(.*?)\])()()()()/g,writeAnchorTag);text=text.replace(/(\[((?:\[[^\]]*\]|[^\[\]])*)\]\([ \t]*()<?((?:\([^)]*\)|[^()\s])*?)>?[ \t]*((['"])(.*?)\6[ \t]*)?\))/g,writeAnchorTag);text=text.replace(/(\[([^\[\]]+)\])()()()()()/g,writeAnchorTag);return text}function writeAnchorTag(wholeMatch,m1,m2,m3,m4,m5,m6,m7){if(m7==undefined){m7=""}var whole_match=m1;var link_text=m2.replace(/:\/\//g,"~P");var link_id=m3.toLowerCase();var url=m4;var title=m7;if(url==""){if(link_id==""){link_id=link_text.toLowerCase().replace(/ ?\n/g," ")}url="#"+link_id;if(g_urls.get(link_id)!=undefined){url=g_urls.get(link_id);if(g_titles.get(link_id)!=undefined){title=g_titles.get(link_id)}}else{if(whole_match.search(/\(\s*\)$/m)>-1){url=""}else{return whole_match}}}url=encodeProblemUrlChars(url);url=escapeCharacters(url,"*_");var result='<a href="'+url+'"';if(title!=""){title=attributeEncode(title);title=escapeCharacters(title,"*_");result+=' title="'+title+'"'}result+=">"+link_text+"</a>";return result}function _DoImages(text){text=text.replace(/(!\[(.*?)\][ ]?(?:\n[ ]*)?\[(.*?)\])()()()()/g,writeImageTag);text=text.replace(/(!\[(.*?)\]\s?\([ \t]*()<?(\S+?)>?[ \t]*((['"])(.*?)\6[ \t]*)?\))/g,writeImageTag);return text}function attributeEncode(text){return text.replace(/>/g,"&gt;").replace(/</g,"&lt;").replace(/"/g,"&quot;")}function writeImageTag(wholeMatch,m1,m2,m3,m4,m5,m6,m7){var whole_match=m1;var alt_text=m2;var link_id=m3.toLowerCase();var url=m4;var title=m7;if(!title){title=""}if(url==""){if(link_id==""){link_id=alt_text.toLowerCase().replace(/ ?\n/g," ")}url="#"+link_id;if(g_urls.get(link_id)!=undefined){url=g_urls.get(link_id);if(g_titles.get(link_id)!=undefined){title=g_titles.get(link_id)}}else{return whole_match}}alt_text=escapeCharacters(attributeEncode(alt_text),"*_[]()");url=escapeCharacters(url,"*_");var result='<img src="'+url+'" alt="'+alt_text+'"';title=attributeEncode(title);title=escapeCharacters(title,"*_");result+=' title="'+title+'"';result+=" />";return result}function _DoHeaders(text){text=text.replace(/^(.+)[ \t]*\n=+[ \t]*\n+/gm,function(wholeMatch,m1){return"<h1>"+_RunSpanGamut(m1)+"</h1>\n\n"});text=text.replace(/^(.+)[ \t]*\n-+[ \t]*\n+/gm,function(matchFound,m1){return"<h2>"+_RunSpanGamut(m1)+"</h2>\n\n"});text=text.replace(/^(\#{1,6})[ \t]*(.+?)[ \t]*\#*\n+/gm,function(wholeMatch,m1,m2){var h_level=m1.length;return"<h"+h_level+">"+_RunSpanGamut(m2)+"</h"+h_level+">\n\n"});return text}function _DoLists(text,isInsideParagraphlessListItem){text+="~0";var whole_list=/^(([ ]{0,3}([*+-]|\d+[.])[ \t]+)[^\r]+?(~0|\n{2,}(?=\S)(?![ \t]*(?:[*+-]|\d+[.])[ \t]+)))/gm;if(g_list_level){text=text.replace(whole_list,function(wholeMatch,m1,m2){var list=m1;var list_type=(m2.search(/[*+-]/g)>-1)?"ul":"ol";var result=_ProcessListItems(list,list_type,isInsideParagraphlessListItem);result=result.replace(/\s+$/,"");result="<"+list_type+">"+result+"</"+list_type+">\n";return result})}else{whole_list=/(\n\n|^\n?)(([ ]{0,3}([*+-]|\d+[.])[ \t]+)[^\r]+?(~0|\n{2,}(?=\S)(?![ \t]*(?:[*+-]|\d+[.])[ \t]+)))/g;text=text.replace(whole_list,function(wholeMatch,m1,m2,m3){var runup=m1;var list=m2;var list_type=(m3.search(/[*+-]/g)>-1)?"ul":"ol";var result=_ProcessListItems(list,list_type);result=runup+"<"+list_type+">\n"+result+"</"+list_type+">\n";return result})}text=text.replace(/~0/,"");return text}var _listItemMarkers={ol:"\\d+[.]",ul:"[*+-]"};function _ProcessListItems(list_str,list_type,isInsideParagraphlessListItem){g_list_level++;list_str=list_str.replace(/\n{2,}$/,"\n");list_str+="~0";var marker=_listItemMarkers[list_type];var re=new RegExp("(^[ \\t]*)("+marker+")[ \\t]+([^\\r]+?(\\n+))(?=(~0|\\1("+marker+")[ \\t]+))","gm");var last_item_had_a_double_newline=false;list_str=list_str.replace(re,function(wholeMatch,m1,m2,m3){var item=m3;var leading_space=m1;var ends_with_double_newline=/\n\n$/.test(item);var contains_double_newline=ends_with_double_newline||item.search(/\n{2,}/)>-1;if(contains_double_newline||last_item_had_a_double_newline){item=_RunBlockGamut(_Outdent(item),true)}else{item=_DoLists(_Outdent(item),true);item=item.replace(/\n$/,"");if(!isInsideParagraphlessListItem){item=_RunSpanGamut(item)}}last_item_had_a_double_newline=ends_with_double_newline;return"<li>"+item+"</li>\n"});list_str=list_str.replace(/~0/g,"");g_list_level--;return list_str}function _DoCodeBlocks(text){text+="~0";text=text.replace(/(?:\n\n|^\n?)((?:(?:[ ]{4}|\t).*\n+)+)(\n*[ ]{0,3}[^ \t\n]|(?=~0))/g,function(wholeMatch,m1,m2){var codeblock=m1;var nextChar=m2;codeblock=_EncodeCode(_Outdent(codeblock));codeblock=_Detab(codeblock);codeblock=codeblock.replace(/^\n+/g,"");codeblock=codeblock.replace(/\n+$/g,"");codeblock="<pre><code>"+codeblock+"\n</code></pre>";return"\n\n"+codeblock+"\n\n"+nextChar});text=text.replace(/~0/,"");return text}function hashBlock(text){text=text.replace(/(^\n+|\n+$)/g,"");return"\n\n~K"+(g_html_blocks.push(text)-1)+"K\n\n"
}function _DoCodeSpans(text){text=text.replace(/(^|[^\\])(`+)([^\r]*?[^`])\2(?!`)/gm,function(wholeMatch,m1,m2,m3,m4){var c=m3;c=c.replace(/^([ \t]*)/g,"");c=c.replace(/[ \t]*$/g,"");c=_EncodeCode(c);c=c.replace(/:\/\//g,"~P");return m1+"<code>"+c+"</code>"});return text}function _EncodeCode(text){text=text.replace(/&/g,"&amp;");text=text.replace(/</g,"&lt;");text=text.replace(/>/g,"&gt;");text=escapeCharacters(text,"*_{}[]\\",false);return text}function _DoItalicsAndBold(text){text=text.replace(/([\W_]|^)(\*\*|__)(?=\S)([^\r]*?\S[\*_]*)\2([\W_]|$)/g,"$1<strong>$3</strong>$4");text=text.replace(/([\W_]|^)(\*|_)(?=\S)([^\r\*_]*?\S)\2([\W_]|$)/g,"$1<em>$3</em>$4");return text}function _DoBlockQuotes(text){text=text.replace(/((^[ \t]*>[ \t]?.+\n(.+\n)*\n*)+)/gm,function(wholeMatch,m1){var bq=m1;bq=bq.replace(/^[ \t]*>[ \t]?/gm,"~0");bq=bq.replace(/~0/g,"");bq=bq.replace(/^[ \t]+$/gm,"");bq=_RunBlockGamut(bq);bq=bq.replace(/(^|\n)/g,"$1  ");bq=bq.replace(/(\s*<pre>[^\r]+?<\/pre>)/gm,function(wholeMatch,m1){var pre=m1;pre=pre.replace(/^  /mg,"~0");pre=pre.replace(/~0/g,"");return pre});return hashBlock("<blockquote>\n"+bq+"\n</blockquote>")});return text}function _FormParagraphs(text,doNotUnhash){text=text.replace(/^\n+/g,"");text=text.replace(/\n+$/g,"");var grafs=text.split(/\n{2,}/g);var grafsOut=[];var markerRe=/~K(\d+)K/;var end=grafs.length;for(var i=0;i<end;i++){var str=grafs[i];if(markerRe.test(str)){grafsOut.push(str)}else{if(/\S/.test(str)){str=_RunSpanGamut(str);str=str.replace(/^([ \t]*)/g,"<p>");str+="</p>";grafsOut.push(str)}}}if(!doNotUnhash){end=grafsOut.length;for(var i=0;i<end;i++){var foundAny=true;while(foundAny){foundAny=false;grafsOut[i]=grafsOut[i].replace(/~K(\d+)K/g,function(wholeMatch,id){foundAny=true;return g_html_blocks[id]})}}}return grafsOut.join("\n\n")}function _EncodeAmpsAndAngles(text){text=text.replace(/&(?!#?[xX]?(?:[0-9a-fA-F]+|\w+);)/g,"&amp;");text=text.replace(/<(?![a-z\/?!]|~D)/gi,"&lt;");return text}function _EncodeBackslashEscapes(text){text=text.replace(/\\(\\)/g,escapeCharacters_callback);text=text.replace(/\\([`*_{}\[\]()>#+-.!])/g,escapeCharacters_callback);return text}var charInsideUrl="[-A-Z0-9+&@#/%?=~_|[\\]()!:,.;]",charEndingUrl="[-A-Z0-9+&@#/%=~_|[\\])]",autoLinkRegex=new RegExp('(="|<)?\\b(https?|ftp)(://'+charInsideUrl+"*"+charEndingUrl+")(?=$|\\W)","gi"),endCharRegex=new RegExp(charEndingUrl,"i");function handleTrailingParens(wholeMatch,lookbehind,protocol,link){if(lookbehind){return wholeMatch}if(link.charAt(link.length-1)!==")"){return"<"+protocol+link+">"}var parens=link.match(/[()]/g);var level=0;for(var i=0;i<parens.length;i++){if(parens[i]==="("){if(level<=0){level=1}else{level++}}else{level--}}var tail="";if(level<0){var re=new RegExp("\\){1,"+(-level)+"}$");link=link.replace(re,function(trailingParens){tail=trailingParens;return""})}if(tail){var lastChar=link.charAt(link.length-1);if(!endCharRegex.test(lastChar)){tail=lastChar+tail;link=link.substr(0,link.length-1)}}return"<"+protocol+link+">"+tail}function _DoAutoLinks(text){text=text.replace(autoLinkRegex,handleTrailingParens);var replacer=function(wholematch,m1){return'<a href="'+m1+'">'+pluginHooks.plainLinkText(m1)+"</a>"};text=text.replace(/<((https?|ftp):[^'">\s]+)>/gi,replacer);return text}function _UnescapeSpecialChars(text){text=text.replace(/~E(\d+)E/g,function(wholeMatch,m1){var charCodeToReplace=parseInt(m1);return String.fromCharCode(charCodeToReplace)});return text}function _Outdent(text){text=text.replace(/^(\t|[ ]{1,4})/gm,"~0");text=text.replace(/~0/g,"");return text}function _Detab(text){if(!/\t/.test(text)){return text}var spaces=["    ","   ","  "," "],skew=0,v;return text.replace(/[\n\t]/g,function(match,offset){if(match==="\n"){skew=offset+1;return match}v=(offset-skew)%4;skew=offset+1;return spaces[v]})}var _problemUrlChars=/(?:["'*()[\]:]|~D)/g;function encodeProblemUrlChars(url){if(!url){return""}var len=url.length;return url.replace(_problemUrlChars,function(match,offset){if(match=="~D"){return"%24"}if(match==":"){return":"}return"%"+match.charCodeAt(0).toString(16)})}function escapeCharacters(text,charsToEscape,afterBackslash){var regexString="(["+charsToEscape.replace(/([\[\]\\])/g,"\\$1")+"])";if(afterBackslash){regexString="\\\\"+regexString}var regex=new RegExp(regexString,"g");text=text.replace(regex,escapeCharacters_callback);return text}function escapeCharacters_callback(wholeMatch,m1){var charCodeToEscape=m1.charCodeAt(0);return"~E"+charCodeToEscape+"E"}}})();

// Markdown.Extra.js
(function(){var inlineTags=new RegExp(["^(<\\/?(a|abbr|acronym|applet|area|b|basefont|","bdo|big|button|cite|code|del|dfn|em|figcaption|","font|i|iframe|img|input|ins|kbd|label|map|","mark|meter|object|param|progress|q|ruby|rp|rt|s|","samp|script|select|small|span|strike|strong|","sub|sup|textarea|time|tt|u|var|wbr)[^>]*>|","<(br)\\s?\\/?>)$"].join(""),"i");if(!Array.indexOf){Array.prototype.indexOf=function(obj){for(var i=0;i<this.length;i++){if(this[i]==obj){return i}}return -1}}function trim(str){return str.replace(/^\s+|\s+$/g,"")}function rtrim(str){return str.replace(/\s+$/g,"")}function outdent(text){return text.replace(new RegExp("^(\\t|[ ]{1,4})","gm"),"")}function contains(str,substr){return str.indexOf(substr)!=-1}function sanitizeHtml(html,whitelist){return html.replace(/<[^>]*>?/gi,function(tag){return tag.match(whitelist)?tag:""})}function union(x,y){var obj={};for(var i=0;i<x.length;i++){obj[x[i]]=x[i]}for(i=0;i<y.length;i++){obj[y[i]]=y[i]}var res=[];for(var k in obj){if(obj.hasOwnProperty(k)){res.push(obj[k])}}return res}function addAnchors(text){if(text.charAt(0)!="\x02"){text="\x02"+text}if(text.charAt(text.length-1)!="\x03"){text=text+"\x03"}return text}function removeAnchors(text){if(text.charAt(0)=="\x02"){text=text.substr(1)}if(text.charAt(text.length-1)=="\x03"){text=text.substr(0,text.length-1)}return text}function convertSpans(text,extra){return sanitizeHtml(convertAll(text,extra),inlineTags)}function convertAll(text,extra){var result=extra.blockGamutHookCallback(text);result=unescapeSpecialChars(result);result=result.replace(/~D/g,"$$").replace(/~T/g,"~");result=extra.previousPostConversion(result);return result}function processEscapesStep1(text){return text.replace(/\\\|/g,"~I").replace(/\\:/g,"~i")}function processEscapesStep2(text){return text.replace(/~I/g,"|").replace(/~i/g,":")}function unescapeSpecialChars(text){text=text.replace(/~E(\d+)E/g,function(wholeMatch,m1){var charCodeToReplace=parseInt(m1);return String.fromCharCode(charCodeToReplace)});return text}function slugify(text){return text.toLowerCase().replace(/\s+/g,"-").replace(/[^\w\-]+/g,"").replace(/\-\-+/g,"-").replace(/^-+/,"").replace(/-+$/,"")}Markdown.Extra=function(){this.converter=null;this.hashBlocks=[];this.footnotes={};this.usedFootnotes=[];this.attributeBlocks=false;this.googleCodePrettify=false;this.highlightJs=false;this.tableClass="";this.tabWidth=4};Markdown.Extra.init=function(converter,options){var extra=new Markdown.Extra();var postNormalizationTransformations=[];var preBlockGamutTransformations=[];var postSpanGamutTransformations=[];var postConversionTransformations=["unHashExtraBlocks"];options=options||{};options.extensions=options.extensions||["all"];if(contains(options.extensions,"all")){options.extensions=["tables","fenced_code_gfm","def_list","attr_list","footnotes","smartypants","strikethrough","newlines"]}preBlockGamutTransformations.push("wrapHeaders");if(contains(options.extensions,"attr_list")){postNormalizationTransformations.push("hashFcbAttributeBlocks");preBlockGamutTransformations.push("hashHeaderAttributeBlocks");postConversionTransformations.push("applyAttributeBlocks");extra.attributeBlocks=true}if(contains(options.extensions,"fenced_code_gfm")){preBlockGamutTransformations.push("fencedCodeBlocks");postNormalizationTransformations.push("fencedCodeBlocks")}if(contains(options.extensions,"tables")){preBlockGamutTransformations.push("tables")}if(contains(options.extensions,"def_list")){preBlockGamutTransformations.push("definitionLists")}if(contains(options.extensions,"footnotes")){postNormalizationTransformations.push("stripFootnoteDefinitions");preBlockGamutTransformations.push("doFootnotes");postConversionTransformations.push("printFootnotes")}if(contains(options.extensions,"smartypants")){postConversionTransformations.push("runSmartyPants")}if(contains(options.extensions,"strikethrough")){postSpanGamutTransformations.push("strikethrough")}if(contains(options.extensions,"newlines")){postSpanGamutTransformations.push("newlines")}converter.hooks.chain("postNormalization",function(text){return extra.doTransform(postNormalizationTransformations,text)+"\n"});converter.hooks.chain("preBlockGamut",function(text,blockGamutHookCallback){extra.blockGamutHookCallback=blockGamutHookCallback;text=processEscapesStep1(text);text=extra.doTransform(preBlockGamutTransformations,text)+"\n";text=processEscapesStep2(text);return text});converter.hooks.chain("postSpanGamut",function(text){return extra.doTransform(postSpanGamutTransformations,text)});extra.previousPostConversion=converter.hooks.postConversion;converter.hooks.chain("postConversion",function(text){text=extra.doTransform(postConversionTransformations,text);extra.hashBlocks=[];extra.footnotes={};extra.usedFootnotes=[];return text});if("highlighter" in options){extra.googleCodePrettify=options.highlighter==="prettify";extra.highlightJs=options.highlighter==="highlight"}if("table_class" in options){extra.tableClass=options.table_class}extra.converter=converter;
return extra};Markdown.Extra.prototype.doTransform=function(transformations,text){for(var i=0;i<transformations.length;i++){text=this[transformations[i]](text)}return text};Markdown.Extra.prototype.hashExtraBlock=function(block){return"\n<p>~X"+(this.hashBlocks.push(block)-1)+"X</p>\n"};Markdown.Extra.prototype.hashExtraInline=function(block){return"~X"+(this.hashBlocks.push(block)-1)+"X"};Markdown.Extra.prototype.unHashExtraBlocks=function(text){var self=this;function recursiveUnHash(){var hasHash=false;text=text.replace(/(?:<p>)?~X(\d+)X(?:<\/p>)?/g,function(wholeMatch,m1){hasHash=true;var key=parseInt(m1,10);return self.hashBlocks[key]});if(hasHash===true){recursiveUnHash()}}recursiveUnHash();return text};Markdown.Extra.prototype.wrapHeaders=function(text){function wrap(text){return"\n"+text+"\n"}text=text.replace(/^.+[ \t]*\n=+[ \t]*\n+/gm,wrap);text=text.replace(/^.+[ \t]*\n-+[ \t]*\n+/gm,wrap);text=text.replace(/^\#{1,6}[ \t]*.+?[ \t]*\#*\n+/gm,wrap);return text};var attrBlock="\\{[ \\t]*((?:[#.][-_:a-zA-Z0-9]+[ \\t]*)+)\\}";var hdrAttributesA=new RegExp("^(#{1,6}.*#{0,6})[ \\t]+"+attrBlock+"[ \\t]*(?:\\n|0x03)","gm");var hdrAttributesB=new RegExp("^(.*)[ \\t]+"+attrBlock+"[ \\t]*\\n"+"(?=[\\-|=]+\\s*(?:\\n|0x03))","gm");var fcbAttributes=new RegExp("^(```[^`\\n]*)[ \\t]+"+attrBlock+"[ \\t]*\\n"+"(?=([\\s\\S]*?)\\n```[ \\t]*(\\n|0x03))","gm");Markdown.Extra.prototype.hashHeaderAttributeBlocks=function(text){var self=this;function attributeCallback(wholeMatch,pre,attr){return"<p>~XX"+(self.hashBlocks.push(attr)-1)+"XX</p>\n"+pre+"\n"}text=text.replace(hdrAttributesA,attributeCallback);text=text.replace(hdrAttributesB,attributeCallback);return text};Markdown.Extra.prototype.hashFcbAttributeBlocks=function(text){var self=this;function attributeCallback(wholeMatch,pre,attr){return"<p>~XX"+(self.hashBlocks.push(attr)-1)+"XX</p>\n"+pre+"\n"}return text.replace(fcbAttributes,attributeCallback)};Markdown.Extra.prototype.applyAttributeBlocks=function(text){var self=this;var blockRe=new RegExp("<p>~XX(\\d+)XX</p>[\\s]*"+'(?:<(h[1-6]|pre)(?: +class="(\\S+)")?(>[\\s\\S]*?</\\2>))',"gm");text=text.replace(blockRe,function(wholeMatch,k,tag,cls,rest){if(!tag){return""}var key=parseInt(k,10);var attributes=self.hashBlocks[key];var id=attributes.match(/#[^\s#.]+/g)||[];var idStr=id[0]?' id="'+id[0].substr(1,id[0].length-1)+'"':"";var classes=attributes.match(/\.[^\s#.]+/g)||[];for(var i=0;i<classes.length;i++){classes[i]=classes[i].substr(1,classes[i].length-1)}var classStr="";if(cls){classes=union(classes,[cls])}if(classes.length>0){classStr=' class="'+classes.join(" ")+'"'}return"<"+tag+idStr+classStr+rest});return text};Markdown.Extra.prototype.tables=function(text){var self=this;var leadingPipe=new RegExp(["^","[ ]{0,3}","[|]","(.+)\\n","[ ]{0,3}","[|]([ ]*[-:]+[-| :]*)\\n","(","(?:[ ]*[|].*\\n?)*",")","(?:\\n|$)"].join(""),"gm");var noLeadingPipe=new RegExp(["^","[ ]{0,3}","(\\S.*[|].*)\\n","[ ]{0,3}","([-:]+[ ]*[|][-| :]*)\\n","(","(?:.*[|].*\\n?)*",")","(?:\\n|$)"].join(""),"gm");text=text.replace(leadingPipe,doTable);text=text.replace(noLeadingPipe,doTable);function doTable(match,header,separator,body,offset,string){header=header.replace(/^ *[|]/m,"");separator=separator.replace(/^ *[|]/m,"");body=body.replace(/^ *[|]/gm,"");header=header.replace(/[|] *$/m,"");separator=separator.replace(/[|] *$/m,"");body=body.replace(/[|] *$/gm,"");alignspecs=separator.split(/ *[|] */);align=[];for(var i=0;i<alignspecs.length;i++){var spec=alignspecs[i];if(spec.match(/^ *-+: *$/m)){align[i]=' align="right"'}else{if(spec.match(/^ *:-+: *$/m)){align[i]=' align="center"'}else{if(spec.match(/^ *:-+ *$/m)){align[i]=' align="left"'}else{align[i]=""}}}}var headers=header.split(/ *[|] */);var colCount=headers.length;var cls=self.tableClass?' class="'+self.tableClass+'"':"";var html=["<table",cls,">\n","<thead>\n","<tr>\n"].join("");for(i=0;i<colCount;i++){var headerHtml=convertSpans(trim(headers[i]),self);html+=["  <th",align[i],">",headerHtml,"</th>\n"].join("")}html+="</tr>\n</thead>\n";var rows=body.split("\n");for(i=0;i<rows.length;i++){if(rows[i].match(/^\s*$/)){continue}var rowCells=rows[i].split(/ *[|] */);var lenDiff=colCount-rowCells.length;for(var j=0;j<lenDiff;j++){rowCells.push("")}html+="<tr>\n";for(j=0;j<colCount;j++){var colHtml=convertSpans(trim(rowCells[j]),self);html+=["  <td",align[j],">",colHtml,"</td>\n"].join("")}html+="</tr>\n"}html+="</table>\n";return self.hashExtraBlock(html)}return text};Markdown.Extra.prototype.stripFootnoteDefinitions=function(text){var self=this;text=text.replace(/\n[ ]{0,3}\[\^(.+?)\]\:[ \t]*\n?([\s\S]*?)\n{1,2}((?=\n[ ]{0,3}\S)|$)/g,function(wholeMatch,m1,m2){m1=slugify(m1);m2+="\n";m2=m2.replace(/^[ ]{0,3}/g,"");self.footnotes[m1]=m2;return"\n"});return text};Markdown.Extra.prototype.doFootnotes=function(text){var self=this;if(self.isConvertingFootnote===true){return text}var footnoteCounter=0;text=text.replace(/\[\^(.+?)\]/g,function(wholeMatch,m1){var id=slugify(m1);var footnote=self.footnotes[id];
if(footnote===undefined){return wholeMatch}footnoteCounter++;self.usedFootnotes.push(id);var html='<a href="#fn:'+id+'" id="fnref:'+id+'" class="footnote">'+footnoteCounter+"</a>";return self.hashExtraInline(html)});return text};Markdown.Extra.prototype.printFootnotes=function(text){var self=this;if(self.usedFootnotes.length===0){return text}text+='\n\n<div class="footnotes">\n<hr>\n<ol>\n\n';for(var i=0;i<self.usedFootnotes.length;i++){var id=self.usedFootnotes[i];var footnote=self.footnotes[id];self.isConvertingFootnote=true;var formattedfootnote=convertSpans(footnote,self);delete self.isConvertingFootnote;text+='<li id="fn:'+id+'">'+formattedfootnote+' <a href="#fnref:'+id+'" title="Return to article" class="reversefootnote">&#8617;</a></li>\n\n'}text+="</ol>\n</div>";return text};Markdown.Extra.prototype.fencedCodeBlocks=function(text){function encodeCode(code){code=code.replace(/&/g,"&amp;");code=code.replace(/</g,"&lt;");code=code.replace(/>/g,"&gt;");code=code.replace(/~D/g,"$$");code=code.replace(/~T/g,"~");return code}var self=this;text=text.replace(/(?:^|\n)```([^`\n]*)\n([\s\S]*?)\n```[ \t]*(?=\n)/g,function(match,m1,m2){var language=trim(m1),codeblock=m2;var preclass=self.googleCodePrettify?' class="prettyprint"':"";var codeclass="";if(language){if(self.googleCodePrettify||self.highlightJs){codeclass=' class="language-'+language+'"'}else{codeclass=' class="'+language+'"'}}var html=["<pre",preclass,"><code",codeclass,">",encodeCode(codeblock),"</code></pre>"].join("");return self.hashExtraBlock(html)});return text};Markdown.Extra.prototype.educatePants=function(text){var self=this;var result="";var blockOffset=0;text.replace(/(?:<!--[\s\S]*?-->)|(<)([a-zA-Z1-6]+)([^\n]*?>)([\s\S]*?)(<\/\2>)/g,function(wholeMatch,m1,m2,m3,m4,m5,offset){var token=text.substring(blockOffset,offset);result+=self.applyPants(token);self.smartyPantsLastChar=result.substring(result.length-1);blockOffset=offset+wholeMatch.length;if(!m1){result+=wholeMatch;return}if(!/code|kbd|pre|script|noscript|iframe|math|ins|del|pre/i.test(m2)){m4=self.educatePants(m4)}else{self.smartyPantsLastChar=m4.substring(m4.length-1)}result+=m1+m2+m3+m4+m5});var lastToken=text.substring(blockOffset);result+=self.applyPants(lastToken);self.smartyPantsLastChar=result.substring(result.length-1);return result};function revertPants(wholeMatch,m1){var blockText=m1;blockText=blockText.replace(/&\#8220;/g,'"');blockText=blockText.replace(/&\#8221;/g,'"');blockText=blockText.replace(/&\#8216;/g,"'");blockText=blockText.replace(/&\#8217;/g,"'");blockText=blockText.replace(/&\#8212;/g,"---");blockText=blockText.replace(/&\#8211;/g,"--");blockText=blockText.replace(/&\#8230;/g,"...");return blockText}Markdown.Extra.prototype.applyPants=function(text){text=text.replace(/---/g,"&#8212;").replace(/--/g,"&#8211;");text=text.replace(/\.\.\./g,"&#8230;").replace(/\.\s\.\s\./g,"&#8230;");text=text.replace(/``/g,"&#8220;").replace(/''/g,"&#8221;");if(/^'$/.test(text)){if(/\S/.test(this.smartyPantsLastChar)){return"&#8217;"}return"&#8216;"}if(/^"$/.test(text)){if(/\S/.test(this.smartyPantsLastChar)){return"&#8221;"}return"&#8220;"}text=text.replace(/^'(?=[!"#\$\%'()*+,\-.\/:;<=>?\@\[\\]\^_`{|}~]\B)/,"&#8217;");text=text.replace(/^"(?=[!"#\$\%'()*+,\-.\/:;<=>?\@\[\\]\^_`{|}~]\B)/,"&#8221;");text=text.replace(/"'(?=\w)/g,"&#8220;&#8216;");text=text.replace(/'"(?=\w)/g,"&#8216;&#8220;");text=text.replace(/'(?=\d{2}s)/g,"&#8217;");text=text.replace(/(\s|&nbsp;|--|&[mn]dash;|&\#8211;|&\#8212;|&\#x201[34];)'(?=\w)/g,"$1&#8216;");text=text.replace(/([^\s\[\{\(\-])'/g,"$1&#8217;");text=text.replace(/'(?=\s|s\b)/g,"&#8217;");text=text.replace(/'/g,"&#8216;");text=text.replace(/(\s|&nbsp;|--|&[mn]dash;|&\#8211;|&\#8212;|&\#x201[34];)"(?=\w)/g,"$1&#8220;");text=text.replace(/([^\s\[\{\(\-])"/g,"$1&#8221;");text=text.replace(/"(?=\s)/g,"&#8221;");text=text.replace(/"/ig,"&#8220;");return text};Markdown.Extra.prototype.runSmartyPants=function(text){this.smartyPantsLastChar="";text=this.educatePants(text);text=text.replace(/(<([a-zA-Z1-6]+)\b([^\n>]*?)(\/)?>)/g,revertPants);return text};Markdown.Extra.prototype.definitionLists=function(text){var wholeList=new RegExp(["(\\x02\\n?|\\n\\n)","(?:","(","(","[ ]{0,3}","((?:[ \\t]*\\S.*\\n)+)","\\n?","[ ]{0,3}:[ ]+",")","([\\s\\S]+?)","(","(?=\\0x03)","|","(?=","\\n{2,}","(?=\\S)","(?!","[ ]{0,3}","(?:\\S.*\\n)+?","\\n?","[ ]{0,3}:[ ]+",")","(?!","[ ]{0,3}:[ ]+",")",")",")",")",")"].join(""),"gm");var self=this;text=addAnchors(text);text=text.replace(wholeList,function(match,pre,list){var result=trim(self.processDefListItems(list));result="<dl>\n"+result+"\n</dl>";return pre+self.hashExtraBlock(result)+"\n\n"});return removeAnchors(text)};Markdown.Extra.prototype.processDefListItems=function(listStr){var self=this;var dt=new RegExp(["(\\x02\\n?|\\n\\n+)","(","[ ]{0,3}","(?![:][ ]|[ ])","(?:\\S.*\\n)+?",")","(?=\\n?[ ]{0,3}:[ ])"].join(""),"gm");var dd=new RegExp(["\\n(\\n+)?","(","[ ]{0,3}","[:][ ]+",")","([\\s\\S]+?)","(?=\\n*","(?:","\\n[ ]{0,3}[:][ ]|","<dt>|\\x03",")",")"].join(""),"gm");
listStr=addAnchors(listStr);listStr=listStr.replace(/\n{2,}(?=\\x03)/,"\n");listStr=listStr.replace(dt,function(match,pre,termsStr){var terms=trim(termsStr).split("\n");var text="";for(var i=0;i<terms.length;i++){var term=terms[i];term=convertSpans(trim(term),self);text+="\n<dt>"+term+"</dt>"}return text+"\n"});listStr=listStr.replace(dd,function(match,leadingLine,markerSpace,def){if(leadingLine||def.match(/\n{2,}/)){def=Array(markerSpace.length+1).join(" ")+def;def=outdent(def)+"\n\n";def="\n"+convertAll(def,self)+"\n"}else{def=rtrim(def);def=convertSpans(outdent(def),self)}return"\n<dd>"+def+"</dd>\n"});return removeAnchors(listStr)};Markdown.Extra.prototype.strikethrough=function(text){return text.replace(/([\W_]|^)~T~T(?=\S)([^\r]*?\S[\*_]*)~T~T([\W_]|$)/g,"$1<del>$2</del>$3")};Markdown.Extra.prototype.newlines=function(text){return text.replace(/(<(?:br|\/li)>)?\n/g,function(wholeMatch,previousTag){return previousTag?wholeMatch:" <br>\n"})}})();


(function() {

	// Create the converter and the editor
	var converter = new Markdown.Converter();
	var options = {
	    _DoItalicsAndBold: function(text) {
	        // Restore original markdown implementation
	        text = text.replace(/(\*\*|__)(?=\S)(.+?[*_]*)(?=\S)\1/g,
	            "<strong>$2</strong>");
	        text = text.replace(/(\*|_)(?=\S)(.+?)(?=\S)\1/g,
	            "<em>$2</em>");
	        return text;
	    }
	};
	converter.setOptions(options);

	function loadJs(src, callback) {
	     var _doc = document.getElementsByTagName('head')[0];
	     var script = document.createElement('script');
	     script.setAttribute('type', 'text/javascript');
	     script.setAttribute('src', src);
	     _doc.appendChild(script);
	     script.onload = script.onreadystatechange = function() {
	        if(!this.readyState || this.readyState=='loaded' || this.readyState=='complete'){
	            callback && callback();
	        }
	        script.onload = script.onreadystatechange = null;
	     }
	}

	function _each(list, callback) {
	    if(list && list.length > 0) {
	        for(var i = 0; i < list.length; i++) {
	            callback(list[i]);
	        }
	    }
	}
	function _has(obj, key) {
	    return hasOwnProperty.call(obj, key);
	};

	// markdown extra
	function initMarkdownExtra() {
		// Create the converter and the editor
		// var converter = new Markdown.Converter();
		var options = {
		    _DoItalicsAndBold: function(text) {
		        // Restore original markdown implementation
		        text = text.replace(/(\*\*|__)(?=\S)(.+?[*_]*)(?=\S)\1/g,
		            "<strong>$2</strong>");
		        text = text.replace(/(\*|_)(?=\S)(.+?)(?=\S)\1/g,
		            "<em>$2</em>");
		        return text;
		    }
		};
		converter.setOptions(options);

		//================
		// markdown exstra

		var markdownExtra = {};
		markdownExtra.config = {
		    extensions: [
		        "fenced_code_gfm",
		        "tables",
		        "def_list",
		        "attr_list",
		        "footnotes",
		        "smartypants",
		        "strikethrough",
		        "newlines"
		    ],
		    intraword: true,
		    comments: true,
		    highlighter: "highlight"
		};
		var extraOptions = {
		    extensions: markdownExtra.config.extensions,
		    highlighter: "prettify"
		};

		if(markdownExtra.config.intraword === true) {
		    var converterOptions = {
		        _DoItalicsAndBold: function(text) {
		            text = text.replace(/([^\w*]|^)(\*\*|__)(?=\S)(.+?[*_]*)(?=\S)\2(?=[^\w*]|$)/g, "$1<strong>$3</strong>");
		            text = text.replace(/([^\w*]|^)(\*|_)(?=\S)(.+?)(?=\S)\2(?=[^\w*]|$)/g, "$1<em>$3</em>");
		            // Redo bold to handle _**word**_
		            text = text.replace(/([^\w*]|^)(\*\*|__)(?=\S)(.+?[*_]*)(?=\S)\2(?=[^\w*]|$)/g, "$1<strong>$3</strong>");
		            return text;
		        }
		    };
		    converter.setOptions(converterOptions);
		}

		if(markdownExtra.config.comments === true) {
		    converter.hooks.chain("postConversion", function(text) {
		        return text.replace(/<!--.*?-->/g, function(wholeMatch) {
		            return wholeMatch.replace(/^<!---(.+?)-?-->$/, ' <span class="comment label label-danger">$1</span> ');
		        });
		    });
		}
		
		// email & todolist
	        converter.hooks.chain("postConversion", function(text) {
	            // email
	            text = text.replace(/<(mailto\:)?([^\s>]+@[^\s>]+\.\S+?)>/g, function(match, mailto, email) {
	                return '<a href="mailto:' + email + '">' + email + '</a>';
	            });
	            // todolist
	            text = text.replace(/<li>(<p>)?\[([ xX]?)\] /g, function(matched, p, b) {
	                p || (p = '');
	                return !(b == 'x' || b == 'X') ? '<li class="m-todo-item m-todo-empty">' + p + '<input type="checkbox" /> ' : '<li class="m-todo-item m-todo-done">' + p + '<input type="checkbox" checked /> '
	            });
	            return text;
	        });

		Markdown.Extra.init(converter, extraOptions);
	}

	//==============
	// toc start

	function initToc() { 
		var toc = {};
	    toc.config = {
	        marker: "\\[(TOC|toc)\\]",
	        maxDepth: 6,
	        button: true,
	    };

	    // TOC element description
	    function TocElement(tagName, anchor, text) {
	        this.tagName = tagName;
	        this.anchor = anchor;
	        this.text = text;
	        this.children = [];
	    }
	    TocElement.prototype.childrenToString = function() {
	        if(this.children.length === 0) {
	            return "";
	        }
	        var result = "<ul>\n";
	        _each(this.children, function(child) {
	            result += child.toString();
	        });
	        result += "</ul>\n";
	        return result;
	    };
	    TocElement.prototype.toString = function() {
	        var result = "<li>";
	        if(this.anchor && this.text) {
	            result += '<a href="#' + this.anchor + '">' + this.text + '</a>';
	        }
	        result += this.childrenToString() + "</li>\n";
	        return result;
	    };

	    // Transform flat list of TocElement into a tree
	    function groupTags(array, level) {
	        level = level || 1;
	        var tagName = "H" + level;
	        var result = [];

	        var currentElement;
	        function pushCurrentElement() {
	            if(currentElement !== undefined) {
	                if(currentElement.children.length > 0) {
	                    currentElement.children = groupTags(currentElement.children, level + 1);
	                }
	                result.push(currentElement);
	            }
	        }

	        _each(array, function(element) {
	            if(element.tagName != tagName) {
	                if(level !== toc.config.maxDepth) {
	                    if(currentElement === undefined) {
	                        currentElement = new TocElement();
	                    }
	                    currentElement.children.push(element);
	                }
	            }
	            else {
	                pushCurrentElement();
	                currentElement = element;
	            }
	        });
	        pushCurrentElement();
	        return result;
	    }

	    var utils = {};
	    var nonWordChars = new RegExp('[^\\p{L}\\p{N}-]', 'g');
	    utils.slugify = function(text) {
	        return text.toLowerCase().replace(/\s/g, '-') // Replace spaces with -
	            .replace(nonWordChars, '') // Remove all non-word chars
	            .replace(/\-\-+/g, '-') // Replace multiple - with single -
	            .replace(/^-+/, '') // Trim - from start of text
	            .replace(/-+$/, ''); // Trim - from end of text
	    };

	    // Build the TOC
	    var previewContentsElt;
	    function buildToc(previewContentsElt) {
	        var anchorList = {};
	        function createAnchor(element) {
	            var id = element.id || utils.slugify(element.textContent) || 'title';
	            var anchor = id;
	            var index = 0;
	            while (_has(anchorList, anchor)) {
	                anchor = id + "-" + (++index);
	            }
	            anchorList[anchor] = true;
	            // Update the id of the element
	            element.id = anchor;
	            return anchor;
	        }

	        var elementList = [];
	        _each(previewContentsElt.querySelectorAll('h1, h2, h3, h4, h5, h6'), function(elt) {
	            elementList.push(new TocElement(elt.tagName, createAnchor(elt), elt.textContent));
	        });
	        elementList = groupTags(elementList);
	        return '<div class="toc">\n<ul>\n' + elementList.join("") + '</ul>\n</div>\n';
	    }

	    toc.convert = function(previewContentsElt) {
	        var tocExp = new RegExp("^\\s*" + toc.config.marker + "\\s*$");
	        var tocEltList = document.querySelectorAll('.table-of-contents, .toc');
	        var htmlToc = buildToc(previewContentsElt);
	        // Replace toc paragraphs
	        _each(previewContentsElt.getElementsByTagName('p'), function(elt) {
	            if(tocExp.test(elt.innerHTML)) {
	                elt.innerHTML = htmlToc;
	            }
	        });
	        // Add toc in the TOC button
	        _each(tocEltList, function(elt) {
	            elt.innerHTML = htmlToc;
	        });
	    }

	    return toc;
	}

	//===========
	// mathjax
	// function initMathJax() {
	// 	// 配置
	// 	MathJax.Hub.Config({
	// 	    skipStartupTypeset: true,
	// 	    "HTML-CSS": {
	// 	        preferredFont: "TeX",
	// 	        availableFonts: [
	// 	            "STIX",
	// 	            "TeX"
	// 	        ],
	// 	        linebreaks: {
	// 	            automatic: true
	// 	        },
	// 	        EqnChunk: 10,
	// 	        imageFont: null
	// 	    },
	// 	    tex2jax: { inlineMath: [["$","$"],["\\\\(","\\\\)"]], displayMath: [["$$","$$"],["\\[","\\]"]], processEscapes: true },
	// 	    TeX: {
	// 	        noUndefined: {
	// 	            attributes: {
	// 	                mathcolor: "red",
	// 	                mathbackground: "#FFEEEE",
	// 	                mathsize: "90%"
	// 	            }
	// 	        },
	// 	        Safe: {
	// 	            allow: {
	// 	                URLs: "safe",
	// 	                classes: "safe",
	// 	                cssIDs: "safe",
	// 	                styles: "safe",
	// 	                fontsize: "all"
	// 	            }
	// 	        }
	// 	    },
	// 	    messageStyle: "none"
	// 	});

	// 	var mathJax = {};
	//     mathJax.config = {
	//         tex    : "{}",
	//         tex2jax: '{ inlineMath: [["$","$"],["\\\\\\\\(","\\\\\\\\)"]], displayMath: [["$$","$$"],["\\\\[","\\\\]"]], processEscapes: true }'
	//     };

	//     mathJax.init = function(p) {
	//         converter.hooks.chain("preConversion", removeMath);
	//         converter.hooks.chain("postConversion", replaceMath);
	//     };

	//     // From math.stackexchange.com...

	//     //
	//     //  The math is in blocks i through j, so
	//     //    collect it into one block and clear the others.
	//     //  Replace &, <, and > by named entities.
	//     //  For IE, put <br> at the ends of comments since IE removes \n.
	//     //  Clear the current math positions and store the index of the
	//     //    math, then push the math string onto the storage array.
	//     //
	//     function processMath(i, j, unescape) {
	//         var block = blocks.slice(i, j + 1).join("")
	//             .replace(/&/g, "&amp;")
	//             .replace(/</g, "&lt;")
	//             .replace(/>/g, "&gt;");
	//         for(HUB.Browser.isMSIE && (block = block.replace(/(%[^\n]*)\n/g, "$1<br/>\n")); j > i;)
	//             blocks[j] = "", j--;
	//         blocks[i] = "@@" + math.length + "@@";
	//         unescape && (block = unescape(block));
	//         math.push(block);
	//         start = end = last = null;
	//     }

	//     function removeMath(text) {
	//         if(!text) {
	//             return;
	//         }
	//         start = end = last = null;
	//         math = [];
	//         var unescape;
	//         if(/`/.test(text)) {
	//             text = text.replace(/~/g, "~T").replace(/(^|[^\\])(`+)([^\n]*?[^`\n])\2(?!`)/gm, function(text) {
	//                 return text.replace(/\$/g, "~D")
	//             });
	//             unescape = function(text) {
	//                 return text.replace(/~([TD])/g,
	//                     function(match, n) {
	//                         return {T: "~", D: "$"}[n]
	//                     })
	//             };
	//         } else {
	//             unescape = function(text) {
	//                 return text
	//             };
	//         }

	//         //
	//         //  The pattern for math delimiters and special symbols
	//         //    needed for searching for math in the page.
	//         //
	//         var splitDelimiter = /(\$\$?|\\(?:begin|end)\{[a-z]*\*?\}|\\[\\{}$]|[{}]|(?:\n\s*)+|@@\d+@@)/i;
	//         var split;

	//         if(3 === "aba".split(/(b)/).length) {
	//             split = function(text, delimiter) {
	//                 return text.split(delimiter)
	//             };
	//         } else {
	//             split = function(text, delimiter) {
	//                 var b = [], c;
	//                 if(!delimiter.global) {
	//                     c = delimiter.toString();
	//                     var d = "";
	//                     c = c.replace(/^\/(.*)\/([im]*)$/, function(a, c, b) {
	//                         d = b;
	//                         return c
	//                     });
	//                     delimiter = RegExp(c, d + "g")
	//                 }
	//                 for(var e = delimiter.lastIndex = 0; c = delimiter.exec(text);) {
	//                     b.push(text.substring(e, c.index));
	//                     b.push.apply(b, c.slice(1));
	//                     e = c.index + c[0].length;
	//                 }
	//                 b.push(text.substring(e));
	//                 return b
	//             };
	//         }

	//         blocks = split(text.replace(/\r\n?/g, "\n"), splitDelimiter);
	//         for(var i = 1, m = blocks.length; i < m; i += 2) {
	//             var block = blocks[i];
	//             if("@" === block.charAt(0)) {
	//                 //
	//                 //  Things that look like our math markers will get
	//                 //  stored and then retrieved along with the math.
	//                 //
	//                 blocks[i] = "@@" + math.length + "@@";
	//                 math.push(block)
	//             } else if(start) {
	//                 // Ignore inline maths that are actually multiline (fixes #136)
	//                 if(end == inline && block.charAt(0) == '\n') {
	//                     if(last) {
	//                         i = last;
	//                         processMath(start, i, unescape);
	//                     }
	//                     start = end = last = null;
	//                     braces = 0;
	//                 }
	//                 //
	//                 //  If we are in math, look for the end delimiter,
	//                 //    but don't go past double line breaks, and
	//                 //    and balance braces within the math.
	//                 //
	//                 else if(block === end) {
	//                     if(braces) {
	//                         last = i
	//                     } else {
	//                         processMath(start, i, unescape)
	//                     }
	//                 } else {
	//                     if(block.match(/\n.*\n/)) {
	//                         if(last) {
	//                             i = last;
	//                             processMath(start, i, unescape);
	//                         }
	//                         start = end = last = null;
	//                         braces = 0;
	//                     } else {
	//                         if("{" === block) {
	//                             braces++
	//                         } else {
	//                             "}" === block && braces && braces--
	//                         }
	//                     }
	//                 }
	//             } else {
	//                 if(block === inline || "$$" === block) {
	//                     start = i;
	//                     end = block;
	//                     braces = 0;
	//                 } else {
	//                     if("begin" === block.substr(1, 5)) {
	//                         start = i;
	//                         end = "\\end" + block.substr(6);
	//                         braces = 0;
	//                     }
	//                 }
	//             }

	//         }
	//         last && processMath(start, last, unescape);
	//         return unescape(blocks.join(""));
	//     }

	// 	    //
	// 	    //  Put back the math strings that were saved,
	// 	    //    and clear the math array (no need to keep it around).
	// 	    //
	// 	    function replaceMath(text) {
	// 	        text = text.replace(/@@(\d+)@@/g, function(match, n) {
	// 	            return math[n]
	// 	        });
	// 	        math = null;
	// 	        return text
	// 	    }

	// 	    //
	// 	    //  This is run to restart MathJax after it has finished
	// 	    //    the previous run (that may have been canceled)
	// 	    //
	// 	    function startMJ(toElem, callback) {
	// 	    	var preview = toElem;
	// 	        pending = false;
	// 	        HUB.cancelTypeset = false;
	// 	        HUB.Queue([
	// 	            "Typeset",
	// 	            HUB,
	// 	            preview
	// 	        ]);
	// 	        // 执行完后, 再执行
	// 	        HUB.Queue(function() {
	// 	        	callback && callback();
	// 	        });
	// 	    }

	// 	    var ready = false, pending = false, preview = null, inline = "$", blocks, start, end, last, braces, math, HUB = MathJax.Hub;

	// 	    //
	// 	    //  Runs after initial typeset
	// 	    //
	// 	    HUB.Queue(function() {
	// 	        ready = true;
	// 	        HUB.processUpdateTime = 50;
	// 	        HUB.Config({"HTML-CSS": {EqnChunk: 10, EqnChunkFactor: 1}, SVG: {EqnChunk: 10, EqnChunkFactor: 1}})
	// 	    });

	//     mathJax.init();
	// 	return {
	// 		convert: startMJ
	// 	}
	// }

	// function initUml() {
	// 	//===========
	// 	// uml
	// 	var umlDiagrams = {};
	//     umlDiagrams.config = {
	//         flowchartOptions: [
	//             '{',
	//             '   "line-width": 2,',
	//             '   "font-family": "sans-serif",',
	//             '   "font-weight": "normal"',
	//             '}'
	//         ].join('\n')
	//     };

	//     var _loadUmlJs = false;

	//     // callback 执行完后执行
	//     umlDiagrams.convert = function(target, callback) {
	//         var previewContentsElt = target;

	//         var sequenceElems = previewContentsElt.querySelectorAll('.prettyprint > .language-sequence');
	//         var flowElems = previewContentsElt.querySelectorAll('.prettyprint > .language-flow');

	//         function convert() { 
	//         	_each(sequenceElems, function(elt) {
	//                 try {
	//                     var diagram = Diagram.parse(elt.textContent);
	//                     var preElt = elt.parentNode;
	//                     var containerElt = crel('div', {
	//                         class: 'sequence-diagram'
	//                     });
	//                     preElt.parentNode.replaceChild(containerElt, preElt);
	//                     diagram.drawSVG(containerElt, {
	//                         theme: 'simple'
	//                     });
	//                 }
	//                 catch(e) {
	//                     console.trace(e);
	//                 }
	//             });
	//             _each(flowElems, function(elt) {
	//                 try {

	//                     var chart = flowchart.parse(elt.textContent);
	//                     var preElt = elt.parentNode;
	//                     var containerElt = crel('div', {
	//                         class: 'flow-chart'
	//                     });
	//                     preElt.parentNode.replaceChild(containerElt, preElt);
	//                     chart.drawSVG(containerElt, JSON.parse(umlDiagrams.config.flowchartOptions));
	//                 }
	//                 catch(e) {
	//                     console.error(e);
	//                 }
	//             });

	//             callback && callback();
	//         }

	//         if(sequenceElems.length > 0 || flowElems.length > 0) {
	//         	if(!_loadUmlJs) {
	// 	        	loadJs('./libs/uml.js', function() {
	// 	        		_loadUmlJs = true;
	// 	                convert();
	// 	            }); 
	//         	} else {
	//         		convert();
	//         	}
	//         } else {
	//         	callback && callback();
	//         }
	//     };

	//     return umlDiagrams;
	// }

	// extra是实时的, 同步进行
	initMarkdownExtra();

	var m;
	window.markdownToHtml = function(mdText, toElem, callback) {
		var _umlEnd = false;
		var _mathJaxEnd = false;

		// 如果是jQuery对象
		if(toElem && !toElem['querySelectorAll'] && toElem['get']) {
			toElem = toElem.get(0);
		}
		if(!toElem || typeof toElem == 'function') {
			callback = toElem;
			toElem = document.createElement('div');
		}
		function _go(mdText, toElem) {
			var htmlParsed = converter.makeHtml(mdText);
			toElem.innerHTML = htmlParsed;

			// 同步执行
			var toc = initToc();
			toc.convert(toElem);

			// 异步执行
			// var umlDiagrams = initUml();
			// umlDiagrams.convert(toElem, function() {
			// 	_umlEnd = true;
			// 	if(_mathJaxEnd) {
			// 		callback && callback(toElem.innerHTML);
			// 	}
			// });
		}

		// 表示有mathjax?
		// 加载mathJax
		// if(mdText.indexOf('$') !== -1) {
		// 	loadJs("./libs/MathJax/MathJax.js?config=TeX-AMS_HTML", function() {
		// 		if(!m) {
		// 			var m = initMathJax();
		// 		}
		// 		// 放到后面, 不然removeMathJax()不运行, bug
		// 		_go(mdText, toElem);
		// 		m.convert(toElem, function() {
		// 			_mathJaxEnd = true;
		// 			if(_umlEnd) {
		// 				callback && callback(toElem.innerHTML);
		// 			}
		// 		});
		// 	});
		// } else {
		// 	_mathJaxEnd = true;
		// 	_go(mdText, toElem);
		// }
		_go(mdText, toElem);
	}

})();
