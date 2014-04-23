#!/usr/bin/ruby

require 'dbi'
require 'pp'
require 'cgi'

puts "Content-type: text/plain\n\n"

oldkeys=%w{
22D52C906D6677F159F10030001CDE6A6B79D401
9F4BD7806EF45700778D8B220064F9FFBB845E97
0D70D69D9D5B00E4E74E674300959FA39C478D49
8C215F25828DA7C07F462399010C2EA6D9309644
684A1F8DC9BBE0DFF3168C9F015427E3A4B47676
7C81E60C442E8FBCD9752F4901998318ADC9BC28
5F6EC41CE863A6C519953A5B01B47334E0D49E99
5F760FDECF30A6206A6F82DD01BB5D753DE37DC0
CE3353BB501F115039D0DC2402E93057444DD950
F18823A1E6E6759102CD850E0312E8C35D8CDA7B
EFD432E05C0B10950669743D032570844D2313D5
B2F9C5E313771B0DC8B0F6B503C0023E05410E97
E37B9BC2CB44DC419FEA4EE103E18C6B83E5110F
AC17A3ECE2C52DC48898CC4B0449EB4D69351387
414EAC7008BC7BC4836E7CA604B3D367B2B831A2
89AFA298E9CCD21216603EC604B7317054AD21B5
32F23DB43D709382E58BD19204D147A595E0A1A1
DB0DF889C81596F203DF0C5104E76310EFC18770
5C8CEBFC806DAA3C2B6BC0BF05048A9B631B4819
FA48D2AF2802F1824D5828230587B26E45F3FBF9
20AD5478A0BC68434A0508A4060C4E63B071C40A
3A0F2F80F79C678A89364FEE06779033A20EBC50
08A90EF89D192196F445097006C05D875BE41F21
1D7FC53F80F852C188F4ED0B07DC563D1F41B907
9B26F48E6F2B0A3F7E33E6B7095E77C579CC6586
EBF6080D59D4008ADF4700D4098DAE47EE3BC279
344C9EC6707AFA176FE260B1099491F791B0D3B7
A801E1F5D96433F6B20A1EDB0A19648B2AE7444E
C2E3EBF1F6E8092F55269A970A300ED090E5CA46
0791D3B89A4C2CDCA31FBD030A62E53437A79149
A8ED2F81B1778FFDA9A69A570B0F2929DF81EE83
8E57F7A8E4B04244C915321B0B5F62A3AAD40AFF
DEE850F81C5AF8208DD629D30BA0EE03EAF19B60
FC9508A6854DDB484B9A8A940BF778679D025E87
D1E29A9D17120E948671834E0CFF30E126257B68
578A87BDBE6D8A04DF7A6EB30D46FE7CD21DF495
96711FD81FCA6831282D6F7A0D4E7DC3FDB4E459
3FFE8447F65F659664906B530DCB394414D4060B
5FDBB1BE9B31D3A8298172850DE8799EA7D6AE79
F2C341368FB175020C0C01B10E5937AC98FAA0AD
F5566852EB92BD779CF137190EA756B5144843F5
BD486B9E4BFAA792CEC5FD7D0EBD65E13C093EEF
FF0784FEE439DA85CAF1EA950F1F76E20D2036AD
4B6DC72F824DCF3B75AE64790FDF48D659B957AE
C0D3F2F00CAC142A46239110100952B5F801A743
EF0D277FACAF0159BBBDDEB510510A738501C7FC
75D8908EBD35E31D94D102EF10557B83807CAC25
51C915494C030E7F2150F1F0111E3AA0BFBCC985
D7A055B647683582B10D3F0C112ECDF2C4A3823E
2123906893F464530847785D1144E4ADA7228C38
72E5703144142EB6F6B44CBD1181703204880A44
CAC10932B6B9876840DBC6AA1239F7098E950E00
445D0A1210E44A0B7352570E1258534C37EC7A69
E922FC882675BF57E8CF5BDF13EE25B5E4B724A4
7BC3013F8489FADC424A07B9141138DDA3E45D66
1F2232EEE56FD048EAEFE47F1467F0D8E1EE3FB1
3CEDBDC64F23BEDAF4892445147F1AEA2DB65596
98E5F9F30D3E63B7F3247065152865FB627CCF95
C644D0B392F48FE44662B5411558944599E81DA0
F36184F18D8232E71832679815E002BA5D8C12EA
49B286EB0461CEAC2E347CC516AD84C0641323B1
5BA68CD42C5798246638C06616E2F4F5FC81E159
9B6432712BA2149AAA03CD481800A1F8B351A900
BC01034DF16542306AD22BC5184452FA268A084D
23F41D24FF2C083DB0932EC2189A3241BC70A6FF
040EB5F784F14FBCCEADADC618A0CC8D5706A4B4
7090A92B18FE79940C364FE418A1B1CF0FE53DD9
CDE122BC836DA44098A853D41BD0E4A5D047CDE1
F9ED8708BE1AF04829275FBD1C26ABEAAB474598
9E8CCC49180D6A1500B400881CEF494673EAE214
6D2D424D824C81DA7D6F1ED41CFA3E8CD7145E30
3C4D08BDE22F1DEDEDA3251B1D3C025FE7DFC3B7
4E68B38EFDB08F638D97F1671D40E113E62B2C45
4FD0E8B755CA8EF008DC9FE11D7365A755815D42
7523647B95E5047547EC2BBA1DA8DA33DDCD686A
2A404678F51A50F269C792F81DBF071150973B91
05BF5B00A17A5B32117FF7361DE4F44021275CC4
E506FDDEA891E826E7137B4A1E198A792782AF55
E67C0D43A75E12A5BB1CFA2F1E32C3DAB7D2F063
339FF8F4DEEFC8AAC77E5D1E1E4F6649EA291785
7579786D41105F4A4D4436911EC237D9534584E8
E91E9F5E01866C52F431333420258B8FA2E31632
D930653A114193BFB8F6163E20D6688259EF5DBC
D3B2A3F5E9EBBDE6A245AA4A212B306C9396865D
F934244D4E26DBDEC9EFBFB721319B944C1A5BE5
655426C9FA10C1D1D3D199C221672570174FEE35
52F6FEBCA7B91895F1B6D35A21A7B53B800969EF
2CA20F848E5C29E3E410438221C747D36A461052
8D2D1F62A4AC9A22FEFCB0DC21EC4FDC84AD676C
43AAF8E27A0E57F4DC7FFD022207C594EC97089D
38FAA231A84DE7C5724850CC2218C81E8E7C03FF
8AE6CDFF6535192FB5B659212262D36F7ADF9466
C38A39C516D7B69F33A3699322C827F735A992E7
716E40B5BEBE5B231C7E17F6233B8A57E4875FF9
2FC3907C20D963EBB234D023236C60C665B4B162
B73B7544AA9E528E838E88F9241061CA50064181
0C04F8720963ADC9AA83882B24A01418AC15B50C
C4402EA201E79D54E6EA61DE24C5CFE4F5521541
F6A14116E18FB6B8B43EA18324FD5E649BF42B07
5A98FF2242DC75277ADE7A58252CC4C873D446C2
73ED4244FD43588620AC2644258494BA917A225E
F3EFB12B23D9D245B7E4BE6D26431938C9ABFBD3
6A2E6A5438F1D1D815136CDF27122D42A674A359
DF3AB6653EEB747A7BDD9B7327D10348DD1B0EF7
CFB557734D191507C4B0A38A27FEA5D163E8BE82
950CA1EA6493A7F64A90AA4D28B295C3F46EADBB
071405537C103CFE2FB44F6D28D3E82917E57327
30DC1D281D7932F55E673ABB28EEB35A3E8DCCC0
269322E7D9255916E0394DD628FC869A289B82B7
DCB911B6BEDF8F3C089B9E6429A0BAFB39A8CCE2
F849E2025D1C194DE62BC6C829BE5D2268FD549F
B030A2BC56A866CFA492E49B29E14F99391B3928
C1F5F24CD5143FEC8BF6A2B12BAEE41F0644FAB7
54656E69E5596466BF3D9F012BF8EE2B7F961564
CFB7C7796BAEE81C3E0571722C045542C9B55DAC
DDF8B22B71418194DB94817A2CEBF138D91EE369
1A21F5B0D8D0CFE381D4E25A2D09E447D0B433DF
110D06BC02F6447AD80CA75E2E4F86BA8B0D42F9
A9F7C81F531A6D888F81203A2E5FDBE0DF67A55E
664EA5A523AFF245748FE1992E9354A1A9FD4821
3755EE8A783F3493A8FF2C8F2F3E069EFEC23FB2
9B0B8CFD05F333F786C7B5DB3056F0EF4C2D3EFA
057F5FF9577DA76DCC2168E7306C483AFF1F7A5C
7A10EB66D499C62996CD88C2307B5229D2A6B810
90B8BFC44A75B88139A3144030EB403B127029F1
925CCE050B76EBBC96375FE731036EC736B861C1
021A833AD2A1015C00103BC9310765FBDF5CE2B4
976448D147ADE1E1E882966C32175C0DC1027A0E
F97AD64AF267663837B603C032286FF8F69C6AC5
F3FA275213277904846DC0DE3233C127E93ADE7B
97A41066E5643748977593C33298C70DE5FFEDE1
E1BA871DA5EA78F3FCBDBA5B330B038B6C63746D
0E9781D69B8816F286F572CE3330A21567209BDE
83C28932B64F1A4EE8A2D7C9342DCB0320021490
395DE808BEADD7215E8220513450ED513FCC2A90
E5D870FFBB267D90D52C56B5347A7D93176015ED
A14997BD188C7F29779E09C1357332C45A827A2D
17C558FC44F27E08DDF13BBC35C3E3FAE91CD250
38841253CD2BCA0BB3432E9F35FC9EEA97AA33D6
3A3ECA3B63E3B1AB24F31BC435FECD3FEB380BE6
E7C65AA9EA49291F7781577F3606C51455BFD024
1B1B2A873F00A7FB40F3526D36CFBA4478916B84
AB92A49538EF7A0EC816A997371A69E3AE3BE9AA
70BC7F9D8C60D2265B7076A23760DBCFFD6645AB
5202EA4B6946AE85149A9BB0376941AB835EB2FF
D00436A90C4BD12002020A3C37E1C17570096AD1
3E7D4267AFD524072A3720AC38A0AD5BCACAB118
32690A0477DA7273BE3F731339220D6E0C1AFFBB
E751A687D8EE4EC30922C4A5394DC5910ED704EA
F607B30B062EA443D33C70E0396DA361FE5F1D7F
B5644BBB97419F11A461719D39A237CB2809E61A
9F1F1EBB29A4918D2C5FFB9C39C979637274AA07
5D4272A835DA48D030B0392B3A65F019CFD42F26
C135F6A86D8F7D25F040E7B43B17BC742A4E3EAA
3A6324104B40422D11111D2C3BBFCF77BD8B050D
F52701E6467CAC15EDC9F9273C8408581A3B48DE
25C32A87055A4275EBB9DFAC3D3E735D83467A34
92720B065DB1A9EEF89001FD3E7434397DD9018D
29634E5DC7918B1114DD72193EA0F86B794F9D7C
D75CE26A13D756EA480838C63ED7095569C0FA93
535E3696356979F4932CB7443F4A8A8FE07F1CF9
61428D079C5B159BC1701F4A40D6F42EF464A695
1CB293CA7D0C4C341B8CCDF340E354D9FA26E2EE
55AB31F837A4104C9C3D7F2740EAFD0BE19F188E
AF6CC0F11E74424BBCD5481440ECC154A8BAC1EA
CD45260A4546C3C0F595F0F64132BF902A385C57
53D732109C90AAB211D805034164D1B3894BB479
EFFDC2C90B84664F14B3096E41B9F4E85B713DF0
3B31C0AD093B6CCD3C6381CE429F015B096C4DD3
BEB43CCC0725E024F531D1DD43148E6D18EA3457
E02EFEF54EC6289E6740D61C431A3CEDA2D7D292
01FA29EF7F5666A86596C50143225D698FC03128
F879F0DEDA780198DD08DC6443EC92504F71955A
DAED39803772421B1AE40F3945458ADCB1E557A0
23F194455C8CB97C983FE504461F3C17C3DC59FA
C3267C307B6DFBF86BA89107462E80ACB7D86E0F
D4199C0239C6A5AFBE2E97AA464DE301B74952A9
D743B1583C04D940A78E8C4246801517A1696D2B
74785B728B8AB530C60BF30346AA1B6A3BFB9FB3
F160CBB903C8425D4BBA79F4491F8FDA5416E5B8
2DA00A3E65263CACE706175A4AD9516B0F932C9C
2B12EC0512C01AE25D559F3F4BA00E72145B6966
B06B023FEAA637DC1E62B0794BE0582590788E11
E114EC83721B6D205D7E16B04BFDBDA66045FB1E
E372BEC0BF6FD89A111005364CA23313A2D8F6BF
35B9B3BFB3E9765FD90E30224CD1F6A6207F2F7A
528627B1F2030DDB90BB37C54D33ACE4C78F687C
975450AAFA49A20BA9C89D714D3C7CA1554FB4C6
AEE01F853E638BAACDF13D184E1875709D309C3B
ACA7C89DD03B52EA7F72AD9A4E8E6FC013282FF2
7F9AD2ADCD3737FD60FD0A114F1A998EDA6AE621
65D7B7CA2B95916F71BE26144F1E0907AEBCE71F
F42F871071C27603A56F16184FDEC6E7E160649A
B9829452CAE00CFAFBF4D1635002EFB1962E3890
9AF5D8B0862D2224400768DF501409C6A0FE58B8
6619634A0F5DB23F6A5FFB6D5028272F3FD29468
9D50042EFF89954364AF01CF509880E3F6A10C2D
A9EBB297CD4424F81CF269A850AA7015A876F581
7C1081B53C566C78AC7D3A2D51602C8D005C3B82
86079AD8227425A11AF9B4D151ACF6AD75BE8097
D54D1AEEB11CCE9BA02BC5DD526F01E8564EE4B6
6C4486ED6D66999F4CCAB79C53E8165BEBEDB32B
16D2E421C2C9B60E9DC466AB5430209C4DD7CC93
BA1C73EB8400716C5B4659C1544D7BB0B12D595A
10CA47C6A071726120E22E0B54703CDE1228EB75
C51BCC4F505F3F8C1C114EDF54A33827B62849B3
828781B3AF3430F1687EAF6454C24FB53B0BB9A9
C4616C2533DABA992A1F0F3C54D4094CF1219B84
3ECB3F9C7D589FCBC939F86D54F52A8713AB03A7
0D128537607E2DF54EFB35A7550F1A003433BD21
198DA17E5B2523BF88B6F7D45586A7DF9F8D08A7
B800BE0B06D78EEBFF980CCF563D7CEC0B191787
5818BF0C98A32B8382BFD3B4564126F229F19BD1
42384696F272C9882A01DB8A575B95B25C33C1B8
E39685B176DB94BE4CE9A40F57E8CE072EAE5D2D
446ECB19D158C53D263691D058395253F829E9E7
1BD5D97CDF5356070609A880583CA816CD98B20A
93AEA3727846B14E0DB38B65589A903470EB0FCE
01E721217DAFB63CA00A039C58C670084597A593
BAC54B28D43695E6F2E0BD115923A0082763483B
96F7A8CCA87F0EB8349701B25A0A399AEA7CF5AD
395CF3A435D3D24713872D9E5A94F3CA0B2713C8
48C4D999F69A4615AF5F28535ACFC4840D62001B
A0C1A28E76270AAB1A57D2385B8FE2F59D1B82F6
B53FE57BD0C1F689FCE256235B9AA5F8801EA932
70E466E41AF7052F7F2C3B275D3CE77FD54F0847
96D40549E44DA739FDAAF2A55D8EE50CF0199162
10D77631735FB57CB8D146D85DCADFE13501E6C5
0F3C34D1E4A38FC6435C01BA5DD5685778D621B4
640FED1488F41A5ED57183585E4EEC2113D0461D
CA4FD469C047165A1A55CCD75E6DEF1C4E2ECA5A
325A3DD1F8D5E51C5D1D83725EB9E72A228A3AE4
DC02BED6463913B817BB6AEC5EC42C53D86A66BA
2A0DD68A657843B60C72C59B5F3931A6E213F1A0
1DA0F1B5FAC435E895C76E28600A553FF666C91D
E6BB7EF8CC4D7FF79D570EAA6042B0B5D3F974DF
3F898015C8F3F388BF34FA0560F960A19A540E39
AB74DDFD5B64218A7D5998F361C749B1C77828D4
D896D80AC0307F05701ED53562B54B8C11404EC3
84DAEA2133802516C38106F7632E3DAD46D9CE5A
19D5773DE17EB7D5C1CB87B763D2D5D907F89BB8
3BE16591C78C2AA431DDAEEF640602273516D372
058963931BFCABEDBEB2091E640E642E2F2F0CDE
2D9353BFB3CEFFA531AA4BF76436436109F34024
498639DAD152050B46999A7166DB5A3626F020F7
5E045B0EA831824D9E5F58716754891DEAAC62DF
29DF544F1BD9548C8F1586EF6770052BB8C1FA69
EEA16E29E9EEE8297499CD796771A2CC718329DC
31A2171EFA6B051885809BD86A08D37C0B4D63D8
2B82A38D1BA5847AA74D6C346AB79ED6C8FDF9C1
D5D39EFC140AB9FF953572D76B37E8DD34B36856
363D3EF3CC922069949C4F116C572D708B143975
E2860604AA3AA178E04870C36C979FDE44E22ACD
A103263A1923373E122746A06DEA9281DA034410
995F58995A9D3DED9D473DD56E69973CF7E8BC63
B3AA8A8AC95EEA2877AA140D6F0B4F8857D68A06
864EEF5DE946DE3814D4D2D46FEA7E2656F06D01
B4BC4D674EDE9802F9A74C17714E66B4496A1827
9328CDA73EF53AC1CDF93A8B71A1FF601BF8DE0F
0AA4EABAF45D81DF35E90F9771A9C91A57159E59
7451CC902F5601DBD4D678F572043670BDE5F1EE
7CE3D0F2EE36C94FAEF6139C721A2B30C154998C
07FB533591FD5ACC4CBC5DBF721EB1B0CEE44978
608B549B779A8DAAED28FEF1725525032224FABC
7394AA3C690660115ED878E672595EB181704B93
96B05A4725393FEDC181A3A3726C2995383F25B5
3F0A12FC0B55A917D79182D372FDC205F6A32A8E
F1B068F9933AAC362A30A7957331B5C057F045DC
F5A8E22B74F721C380A352AA73DF8DAB0A327652
E8DC91A1B7BEE5ABC17247EE742F2A428E635A5E
820F6308F2B08DA24D3EC20E750807B5551BE447
3A6D1E36E58A91CCC372A68E7592489BCC983928
B67ACB32C21FC4FE6EDEC08175E1C1E9710F68E2
C6AEBDCC834C811871A3634176112FBCFCB1DD23
12EDD7B538F5198A4EC4DDBA76266C50FBB1DB53
E959DBA0092A7AD23F41500E7649D1C5B4A4E070
73FE5760EBEA331FC39F83E7769FBF4873014091
807BA7C50D7D81C0C21F1D36775AC806095918D0
7FC70DC0EF31DF837313FE2B77A8F36A3B047084
C7F61E9C32910EADCB8E55987806CD6F133108EA
A97746CDF7094611A44D27FA781C250432EC6F3E
1559FABEB1CE464DAB7F2E7178302C4B8DBFEC2F
4940AE28C5F8E8A35E4D8D287833ECF1B5444815
D604F94B5A4C45E84E8465187985979AE3304051
B66CD97ACE820575D38E8B7B79B0126693701EEF
2B653B348212337FB37E585A79D9469400E0D054
08A97B7D3D133EF23D25D15779E6F6DC888354F7
63311CAEC24642A4A15DF75079FCCFD2B0458F4D
4389F70092A2044E83520EFE7A81833366468D05
8574F8F3947725F5B339896D7A95A5B988784703
D77D6312932FA19CF9CDB8517AFF4B3AC34AA484
BE88B4B38D1F6639580FCCEE7B199D131997E7CF
BF811C95882BE1C26562772D7C811013F5C9708D
190200025DFC856BF146894C7CC5451EA244C858
6F0E1FA1F92FF96EDE2E56C97CD760631557BC10
1E0849A352646367675AD4897D08E5236EB95A6F
9C208F6D50870F9BFF3D4FBD7D46C81CFAA95931
A698CD7FC5ED63FE985273C27D8DDD89C4CF8EC3
AA46F4F2BD5975A4EE4282237DB96D2E36EE0861
A7DBB59A4268DDF2276035947E2F30EEECA94FA8
E79467F1B907425355D9067E7ECDAD406C0084FC
976E747F499C458015CBC0BF7EDE8735DC426429
D4024AF37488165BCC3441477F0CD922EE4C26E8
36CB6E311236B81B3A38054B81377E4A8768B1D2
C2ABED7E865F60C176C47757813FE83A74974824
D1820E3CCB05255CCD9855988143F7EEA5E43EA3
68CB5B3A48FC18F17D79A94681872F9B54C1C1C9
A3C282024F979BAD6ED484D18196A5446BBA3C84
1149DCAB4F2F17C6C458DC7F82091D9A5921B5D8
B733A61DFE90985905ED4B218233A6D22D2F75EF
058E0BBC57E7F03479579D3182944F68EA2D2C41
7961298678142F4C15D2191282F0707088D224B6
D5D098AFB14363734F4178618351C3C268AC5746
24D6980A17E05B155DED1F1D83FFC87BD02F8773
3EEECE2D3F83E4D423551223842CDB7A44779E18
412390227937157C990177E5846A74DB6538F5BF
4C951CEC98B44B68A286FF458489B14D8807529B
56B4B786A62D3EA134CF264C84C1C77BC0B10A5B
D363691F1C4E70D71B9E07DE84E64AA009FC015C
42B8C61FF6EACE10BCBAFAE9850BA2DE13FEFC40
90750D0B5211C8962AD67137853575EC4A08B2FE
20F49C926AA6C046F2B05F0885672E5DDDA51280
F3A06327D7557480440C458685E8FBFCF0B27113
756D73EF1C11668A5E495F5C8607903DBDF0AAD0
92228732859D25CC2560B617867BF9A9FBD3EB8E
0416EDEF91138372D4970EE78745DD787582C21A
26C536DCA9AB1F3F640EE0308771348338015E7E
7345F2F751F07700FEB7FE2087D5E190EBC73D63
226D697EFF42A4AC7317C40688BBD7DDBD88CDAC
4100B65052BF970E4F1F9867894C303CEBE31EF5
06BD0E92721EA1C6AA4D9F2889980D29C0DDC83F
ECF3ADB2B82A839E1404D80489B3EF32CAEAAF03
E6445A655AF81C0F9DECA73589CD4B21607559E6
F883D8A8FB042D6731BD635D8A1D99BF0D7CA701
AD46C888F587F8A3A6DA32618A2C7DC28BD4A489
1B25F91F9E7B5D4F128202D68A838BE4D8480F2E
A681868486470C5D79B9A59D8B9D310A97C398CB
818AE6055310CEB65B08D8C48C7DD3254F6A478E
CF0B10589F1D97102CAD3F858CEEB259B3C281F4
CEE06509A9D42D28D2573EA88CF535F66AA572F7
3BB6E1240643A6156F0068548D11456375C024C8
C83EDA064DA5138578C7B9598DD404FF7ED87D57
E5520FF2E1383E6928B3A1838E055F139B726B71
B8F572F14CC831F9013F7B1E8E62E7F764011A8B
DDBE8A2373481CA7FC9156CC8F3B66A6FC494FC4
D20172742FE1A92AC45CEFAB8F70629AC718D347
E1870B62BFAB87447FEDE31A8F7274F307062A38
0AA3E8791D82F59E77A40096911F4AE686A118E6
C9024BD80CFFBE4529EBA711912924FE3DC29B41
C0BD59FEBBFA2A7E8A41BB3F91374E81825BEF79
7102808A7733C2F3097B161B9222DAB89840105A
EE93BB17DE3DB89F44CE4ECB92BC94766394265E
BD2A847E2C31BC788631CDE592E0BDE7C6002CBD
3D16272FA73AF5B1F91B5D8C9306C9BCDAF1054C
CD0AE4537C92D81065061B7093B991367D61E3E6
DD2937062B8D22A8DEA2C302941C86926F222F1F
69A5548C414511168CA92CB594483FA354DB33D3
1FEA0251FD47DBF5A4062BE7950118DBA895B621
3CDA0ACDA97EC01795A90243951F892C7FED549B
EA71B29645974D8B343E821E962483E15662C734
FA91956AA3DB251EF0B5AC3E96FF6FE4244ACFB7
D9E45378D0F9E4B20622D299976B884B0813569F
93005DC27E876C37ED7BCA9A98083544945348A4
6EF6C284C95D78F60B78FFD3981C5FD7C671257D
67D60A5932836E53F72E9DEE987689619ED101BF
BDC59E6BC8E3B139DAF07E6998A15B3EA6BA423E
1C6E77A082DA2EDBD1B125B498C99E8BDB898410
0C2CE3E83489599A75EF115698EE733A9DE1EEB1
B55E1248ADE6909495BAC7E59946397AE142E6F4
B9FA855DBE54DE19AD27851F995B17866B3B7323
076531CE6223B28C1A644F7A99727C1454ECB8AF
99E8E74E7B4F93AEF32A552399730D5C8A9A3084
E820094883974FDC3CD00EC699D399A1EC36A185
B5EF402B69E791432461ED189A55B33CA71C1E00
7DDF975E73435ACD725E62159A6027DB1A944AD7
BE3D5AF7470A183F0E518C339A8DBEF268396FD2
CF682F046496EFEA663C24419A953C82556ABA51
4491BB79CD5AD94A66814B0C9AA551D966A90DE2
B5E7DDCA01B39BEE841B1E199B46F1FB088F6B8C
71DFD2B345C267FF2B7F06CE9BC7E5DC74886B63
2061020BA49CB3F7810815D09C0E389B3FD25C84
F9F86E60FB2C0EA422BF025F9C10DDE4C6A2EB7E
3641E48643825A1340E7EB439C851C72F12DA065
5CE8ADFA1FDD9DEA6E21DCE19CCBDA1601FA8B4A
47E4BB6FF629245E311677E79D0633E1B6250985
308E81E7B97963BCA0E6ED889D5BD511B7CDA2DC
3F9902038EBCC061F16D2AA19DF99BDA11691130
38378E6102542A8BBF7475959E86D9142C9ED607
6073C8748488BCDAA6A9B7619ED078EF4B3A135C
6C608C2D20FCD4624A97D1089EE43746DE599800
549A598550F2C6DB416F287C9EF854EDFC992520
FBDF66F84CAC5E588EC477E49FCF2CCD3F3E6426
BE65FD1EF4EA08F323D43C6D9FE8B8CD71C5D1A8
51B335E71D4C13261A37E86DA02CDA9F3D08B612
DA06F3E341E999EC18C376DDA108FBC534A26946
190A8C7607743E3130603836A1183F8ED1028C8D
D85B36267C65069E446022FDA1231035532005DA
370350DE7A9F024E0F260D07A18FB40BD4BE1450
A32897E97EA9BAE5A7195812A1B13F2C2C8B195A
12DAD00150FDB751A32CED19A1BCBB2F306CDFF3
CF677AECDC3E11621E32AF6AA217C4C35E2EB5B4
9B3B987BF40E932006190A17A366302EB1DE86CE
6D77976A392AEE47CA4331D3A3F5DC7342000462
3798CF214178565EFDE7480BA43E6D27128287E8
92E42D44336FDF91550823D5A4535199E9F2C747
6665725C400A7EE071500F60A4E2880389BF7E2B
BC8103B7B2891227A02E675AA56BC3DF985BA281
DACF8509A3CAA24DC5FEA588A72FF66C42BD645D
8A306ED1C122B4D524D05137A780421C68021CE4
0FDF0F1869C2AA24B45F1691A84F709AEDD3D779
44A9EDF44076706A22B761A0A88A9AB0864826C3
A7676E0D4B855C1318128733A8CB01F5BE9F70EA
C1A82BE87587215D91EBB015A95C3BECEB88E930
663BD5D71E1C4AB4CD254A3AA975987B1F9FA7EE
48B484D197DD75FB5727B665A9B62CEAC42B63CA
B5963B24A9B200B55CDB636CAAAEC012DD0F6268
1B23D4F88EC0D9020555E438AB8C00CFF8E26537
D9D9754A4BBA2E7D0A0AC024AC2A5FFE00823EC2
8C62F78F73041328C670C347AD295AE1D75F8533
D8C64C2CE88EE5CF873716C4ADE94F6507799E74
08BA6695BF3358B0935624DCAE77E041B9D56A91
96C5012F5F74A5F71FF75291AF29C719124B61FA
4A6B2543679D43B02B635439AFF4670B0F7A8D01
A3602018526B3DFF52BEE5AAB0F7E8C60FCC27C6
754210E3866279DB1123D352B1195000FD46A698
63490CA7D9728AA050A620FEB14BCEFE316DC8FB
86AADB04D2F5CC553A4D940FB1A9DD82DC814B09
198F5EAE4F00F3D1E9A7BC50B1CA92E8A7D86B95
6ADD5093AC6D1072C9129000B1CCD97290267086
EA7DC27F2742024DFB1E8293B24F9D802225848E
1C778E9F923F843174A72CE5B28EBE4FBA98E15D
D02D8C0CADBBA69BBF0F6EADB2B05F45D626ABB6
34F879978BC103F09C43F3D7B3753E4D514B3E7C
B906A53F84E049B66CF782C2B3A02D6623706F87
DC51277EF94DDFFFE156CD85B5022EB582EA653E
79982CB0635F170ADFE9643DB5E01C5DE678D1A1
7F9E800AFC6BA5928914D71FB5F92902090C3B23
1688A3D6F0BDE4DF2E6B06AAB6A9BA6AA59B1171
A110EAE1D7D280765FE0EC0AB6CE704164124E4A
9C0712D92B0C8978C547B98BB72D2AB365B328C6
F3C7DAC35EE02E9D93DF2CC3B7635728153FF940
55782B782151EEB381717DE6B8824687F1968D1B
705A4C887A366A4E6A12CE5AB8CA331F10726171
9A57344C54D3C8610A5F22FCBAA569D0CBF12A6A
1B954398F362AD2DC5E6718BBAB12CF0C7C58F7C
6DE006ED5430A503940ED685BAC78EE5DBA50595
3C77E7F046F8D3653F3873F2BADBEFA9B4D6DE13
8C8D51FB2E4A38ED4ECDFBA9BC5758175230514A
72B4C59ADA78D70E055C129EBC6AFB5BA1EE761C
0E8944762B0B3F32B56A4043BCBBC495718A9256
16A286B6CA6FC9FA6280C9D5BD099FA292DC02A9
87FCDA315F00C8850DC3E28FBD0D4B33A997BA7A
697807F613F7E0A359D1FF95BDC0A0AE06468DEB
75FFFC9F717B526296A20609BDD933B785FEC17F
D792B8A5A567B001C3422613BDF2A2205E3619D3
C8B2CB3E322549BB5ED20002BE3CED47C6CEA0C9
467348C85F3A5A9B2B0D169EBF1E9D1F76D52AC4
19A5031044F274AA16761CFDBF7C793AC9132DDB
4215EA5BBDDA4DD48A7AA125BFCA4B38A824B93F
D966CBDB8E2975D02B1F1633C004F6035912C27E
0DAFEEA41C0CFD21111B5C3FC007DEBB30825345
F067EA2726B9C3FC1486202EC09E1D8995930EDE
737357552CC0B16C4339258FC0A4F11DE06B3F97
DC7B94537F261BF96B219F90C18773559FE8D504
C382DF92991C50061204E0C4C26C97906D4FC66F
D51E60CA98996009F1A4B4CDC2B079FCF5C75256
4B7D218817B6F67C582DCFB0C376A8DAF1BCDB73
F8CB9B2230C25F2B113D2F3DC3DE75AE036BAB8D
753636FE62768F94785D2042C3F8A3A26A8333C6
2BBBA14DDD49D5F38C105F01C40AD676437D328B
C10ED1D0EF700A2ACACF9A3CC490534E75C089FE
732368015D7002442ECE3563C490643655D3A1E9
902B5C62E28D59F0F860C39AC61A895E85EE3E0E
587D9A3EC1D563EAD4245DDEC79838D0436337DD
23499FA0AE0DE2BA9E18560DC7D930259DFFAAD4
1EBA24A7DAAE662C6FF34B37C7F521C122B282CA
F2E1D6829607241FE54C12A8C8B7E935D63469DF
CF67D67A398CD0B8723431C4C97425FBAE4B5D92
03F39777FE54A8F65545EBFBCA07E61412AA1DB8
F6FB223148A9B50C68D718ECCA78CB3E6E76D81D
9F73032EEAC9F7AD951F280ECB668E29A3FD0DF7
6EB39358D8328FE3CDC903A8CB6FA340E7075A54
C3CF4178B8AD5871DD100B17CC1332317C796B7D
1CCFF5B3A16607D3FF6E2212CC254778F28CD102
8A46ADB3FC4B4B24DF1728BACCDFE49B0A0AC927
E807B151497DFFBF88F8C846CCF0D5379F223683
4B50F1E3080C21A291F48BF0CD603B5A2ECF984B
F369DA7EB08B0320562F5D6BCE04080E9456ADE2
709197B8927DAB9F40255A7BCE84E8E795A4F1D6
FA59358BA580CA386695714FCEB14A7A1DDC990D
A3C693AF5805F46B67D596B2CF153232C24B6010
4B74F71B1C2272344249BF53CF62D79438E68E0E
68177B2B2BF382F8C499CB98CF953E76C24B9018
2D31192787D71F249FF91BC5D1065AB38E384AF2
DC6C12B4698D0D907C54380ED115D067AA5FD7AC
8FEFE900783CF175827C2F65D14219877A786561
7ACE0FB07A74F9949B36E1D1D14E8526DC47CA16
0163FBB25BF0E1C8E530944CD152FFDAD06A8654
61A90CB8CE09966D0741880BD1F857D18FE8733D
4F032C3CACA0C02D9BB218E3D203CCA5FDA6B6A9
5ED7B15389C4ED210E8B7F3DD22D9B3D21DB31C5
F36251F76D5185EBAF6875B9D29B1AFCF90FFFE5
88462A803BAE94ED94BA98DCD29BBFFC442E63C2
14DF2E6C0307BE6DAD76A9C0D2BF4AA309C5B094
36E2EDDEC21FEC8F77B87436D362B62A54B99890
6AA2ABD3C802094EF1FF283BD386DEE262EEAD8B
3AAAE18DDBB4C8D056173880D485DD2F5BFA90EC
710F265D7B816542F23CE054D4B7DDF7B16CCA95
C5B81C4D3C1663B2711E4C28D4D8356166F24521
09F05D7A2BB04E77A73C9F84D523A6E660062884
C745FA3527B432A691B33935D573D5B129AB4CDD
D73EEDEC8D5CBE955D9BC6AAD696CA8660B6B958
B282763CE63729B64B024260D722058FC0033D7A
7EE290B21E01D6B3A7520B1BD7595D374B729625
183A70FC47321B8757A5CE82D8377D4EE81E55C1
04AEE62C9502CD34A7DA857BD8DF53FB37E272E8
0EE927C955F192E43809B852D8E0724BB29396EB
F3A5FA523D1DCD1FB05BE328D90A1C75F90F9FF1
87F192C444AA4105B1C4EDECD9959620C00E9159
EE63C471ADBA5D80ADFB1054DA286F326C5F196B
48DFD0003BE71FF8D9C15832DA460E47EE6DC66A
2CD6C838BE77795F5EF13E5BDA91EE7BA58E164F
C7B709D005F838EF9A48CCBDDAD5A719BCC131DE
1FFBF62CFFAB43DDDC81F6AEDAF7350A7EBBD625
CAC6254513564ED7507019B3DB040A13A3D7B9BC
830C56B4125681C54D71CFD1DB4CCC4B2A30D729
137107DF3CF391607905144BDB6414CA204DDF1B
45CFB559828180918469CACDDB71AEFCABA0E8B2
FF7A33E79EF3EB2426E86868DCF8D65B03F35988
B7938AC2CC488357C29939C2DDE35CF15653C9C4
8C45D3765B3907517FA5F866DEEC8C09DE415B0E
79D417AFF510BE814C308BCDDF45A8055D07E95C
F9AB00C13E3A8125DD3FDF1CDF79A374B4071A65
A86D7CED4E8C17F64457FD1ADFEDBB2225BCD5BF
7FC1A0854909BCCDBE6C102DDFFC022A6B113E44
6583A11F1428FCDD65FCC7B5E0CD3CDC59B2D9A0
5230575778003789D68AFD38E1060E07B25A5CF1
B2A37622D32A0D1CCE3F3DF2E17AD7B5090DD8D5
190E48D751174F42ABAC4DD7E2624966A269D927
7D9BD9F6F21953332D1DC4F9E283C86878398A01
0BA3FF69645D021DE0542DC4E28450F601D3AB93
31B8BF834898E26D19354C5DE2EDE84371473F66
FCA1A9FEC037B51928CF9FC2E361D392B0AA8450
424626C56C4AA9DB11194C07E3AA82D81B352C01
0DBD8FCC4F6B8D418F4363A1E43B153CCB467E27
6F1F40039E09BD7A8099C5F3E48B65B54B394F7E
DCAF16D5BB56B970A8F9EC88E4CE6199D0980A99
784F4E389A576829378B105BE4D7E0EA4C40410A
BB1838728F40B7E63BFCD67AE52707E90485EFCD
2F18947301F75240A6E8B1BCE5350AE06087D2F8
08505F45081052B18F5E5022E53B8AA696552D63
74FD81B904BA906F79712714E676B867F8D54259
2BABC6254E66E7B8450AC3E1E6AA90171392B174
F2296392EC63C9A7F5B0E809E6EF68372CFD1C38
586377100EB11C2DAD7E1B3EE74D29B82BE16D01
0F1E5C1F1D3DF7DBAEE04288E7FF2E5B634F9A20
253A40766A3BCCE2A426DEF5E80FC4C1A8061F32
FA6925548C9AC52C311B4A9DE890DD36AF2A4968
3F437485B057EFEF2F2FA12BE90112A72B05B73A
1B65C26BDA0A507B8E342E69E93ABC69A7BE5AB0
72076C7376397FBEEDE66EA8E9B0C69E268462E3
9A8DC9566B8148801557A82BEA3FAC90FAEEB4A9
1573D54473C3988F00963E4FEA4C661F2B46A27C
E4E44DEECDA10D901DD99DA4EA7ED2A341954920
C3ED6F9C2E5B4CFA6030E409EB7CBAA680C83E8E
FAA6D8592F0BAED7C3329F7AEBAD6E5CBAC59E39
96747EE24AC6F5EF3C5752C3EC326810CD5626F0
050C2D2FA95A25BBB61FCD16EC3BCAC4137A955E
52C344D60D02CD9B07031447ED3A39E393674C40
5B9F587FBC5CD82350CE4DB0ED93CA29124B26F3
5028E73900DC3E7BDE6C6ED6EDC63044925288BE
190852B94A166EC274D1C03BEDFB700537155778
54225C61F6B706FB7E043738EE25DE3F1CDB0FE3
1624F9A558458C84DB055684EE3A9F0281C2A4AC
60D04388E3853643807B9507EE491C3E0123F2F2
0FA6DCF3C1B87FC2E637B9D4EE50AA3CDD81604C
54F6D1B12EE181CD65E3A1D3EEA2EFA277DCE083
20FCAD60E8C8D2EB064A8F5BEED8D4CC1DEB8EAE
767C80485684A391A1576818EF653E8D5AF4C462
B7DF3C4162808B749627DA84EF7FDB35D6806145
A74A703C8FC9198EB12DD83DEFA55436964199E2
F8919C6A91DC3A35AE1CC0BFF09B1EEDDEBA6F3E
41352A3B4726ACC590940097F0A98A4C4CD6E3D2
1DCB88A1B90EADFE318CEBE4F0E9F6BA3CD95104
AC1185A49C0BE1F8180D3B07F118B5951E161AFB
802EB746852F21A39239C111F16961C8CC8D7957
12F89C0389D3DB4A9972C24AF19BA618924C0C26
24F2720EC693FEA0A564F8DEF1D2CCC8497A176D
ADEE56831C993257F41DA3F2F20FAC0B7B8357E5
7DB291A3CA1BE7078065B873F36D89424DB97694
2A111B38C4DB23BFA7C7E19DF3E85400D70AAFF9
F58548B594504CC6AD853EC3F41FED8E33FC40A4
CC918F028CDE911A933FAE52F4E66A7CC20DF273
FFFDBD99A508A2372B26C623F5CE68EB6FF0ABF2
314E3B2D605A6EB35A7D8119F628EB934743206C
FF13C2E9F9C3DF547C4FEAC1F675AAE2D2AB2220
F6A7EF7E468870C66B37A8EFF6B09645B24BF200
935E449D2B0843E4FF6CE510F6EE83B9DF901724
26C0976C594BE3C7A5A392DDF7180D26AEDAA642
CEC86BB4A0BA9D0F90397CAEF8358FA2F2833C93
3CAB9397E835E2E95289A0C0F85EBF46258D8781
C643C2338B7D7A1742877D03F892981B6258629A
7E74053E142DB9CC313111B8F8C41B2CF7142EC2
AC3A464ADF876468F63DCCB2F8D31F49DEB0EC31
B7A728128390BBB21AC66F9EF9935424B1DF9A57
8B325F49B8A5F2039A837E9CF9CA01D5E26A6F28
A8B90F6902FD86E7D339C9A6FA96A148004DA6B4
E93E504310EF5D5F5D64E1EBFB13343857E3E888
25C0E61BDC474BA7204E62F5FB1B3D632252FA1A
39272F04C8E560DC056CE2F3FC8D76733C86260F
7285A1EBA8633EE26BB23D41FDDAB37AD935CEBA
0CA24B9714437CBD3628A341FE87DFAD2C0FCD1A
}

oldkeys_dm = %w{
AE927C799353DB4609B273BC085A9B327C2CAEB8
8F25B3364522B304DFA0E1C70F8033F0BACAB6C2
0D86778C9DDFC4600BBBDB1710A46FFB90D53618
37DB5257FCBA84C9A85490E31571C4CFF6E7A452
C27996B984045CB08A58F38F17A165D5F0A25F0E
AD0AC5DFC4264F035D532BDB18D8A4E2D0EDB64D
20BB3CCECFE50A6139A57E9A1BB375334D750376
8B384A47C5B2C59735CC50EB1F2B7AB205B99DD6
3E73FA1F5C57600504394D751FD2BF96F5CC22A4
0F65B88F1EB8928A3DF9D76C28466F1A54C2A185
57AD42ECB22F67D713AF1AB2290FBE52EEA07609
EABACA02C85779DA53410F362E979FF624EDC406
22886BA97159CA6B7121B030363BCAEC94D6CBB0
E4D7FFE905DC76C272F331D5381D2AC78124B100
3C0B6EB0AB2729E8CE2255A7385AE490868EFA66
4617E5FBC56DACB67C8CDE643A4CB2701A89CC23
4656B626E481EE4E7EC572DA46CC5C63F318A56A
5E787F8DB58F02AF5C63C9DD4A2254641FE1B08B
11F4DE9F1FAF6581F2BA3496548662D00E41645E
B11E2D9D2861F45188B200A158B29F8CF74EC6C8
AA9E56639CAEF8FE2370F01D5C3AA7E83487EC71
ECA5F5232FE1F8E3B1303ACB5E326303C98B5D5D
6B68F86185847D7BC43F68D566611D57D487A1EE
C70CD7B8ED93717E035435DE67DA2448A9A3EDD5
73571E85C19F4281D8C97AA86CA41A7743B8D6C8
A5F9C48C4059B6886CC57A426F7818A9B98F62B1
126DAF6BCC84D7D05D6A4C9A71956D47CD9B9806
F190A93A75D2BF6B2B3C1C3E7C64D4A494D68544
B86CB5487CC4B58F0CA3856E7EE852DEE6B78725
8EBE7AD5641958AE1C1AEEEC85F15E59F01DFE92
0D26AA8906A47C1A9665C0078D67107C0802640F
4C004DF209F263ABFD8638C795DE059D8D7FCA91
C1FABEE40A628709CCFB7D2C964D005C0CA7686C
218F6A654090B4086FD42E9AA35A4E6EF00175CA
E3DDD7D41C2FDAF66C55C224A4FEBB980AF24BF4
8E880721AB4AC2A06E74C7B4A677D7EC95DA8EA9
B5BCBDDE7CA813D4F6A3D135A7771D09B55C9C2B
1DF5BE70237E349E798391A3AC4F466D7D1D3A2F
92429807C9853C0744A68B9AAE07828059A53CC1
160853D573C1690115FA4B78B012AD8CF19F599F
3412EA181277354B991BC869B2197FDB5EA01078
9CFE12B0791A4267887F520CB7AC2E51BD41714B
DF2AE3BD59149112195F8740BDF4BD5D420F3009
945C748020CE177DCCD56E44C1ED266701F55480
0BCA751BEEB81FBC7661BEA5C412AF7E994376FD
7F6A9F44282018E218DE24AACF49D0E68A2FAFBC
34CA12A3C6F8B15672C2D0D7D286CE0C0C62B791
289F7CE0A310DC5671A591EBDE6B4AC392742B33
225DF1029718A1B08D837BDFEA11D609624D95E5
B7AD97201D3442F4345DEC16ECEEDDA00BA7D094
0896F05999C906DBB3BCD04BF1E30FE50CA6B4AA
FC3D302E02E469C30AA89067F7D931D4B882EBD7
709F54E4ECF3195623326AE3F82E5CC04B2B2B9E
7E3DEECF80AC4C3CFA0BD138FC2D1E5077F726CD
}

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

sth = dbh.prepare("select distinct date, signed_by_name, signed_by_email, key_id, fingerprint, source from upload_history uh1 where (fingerprint, date) in (select fingerprint, max(date) from upload_history uh2 where date < '2015-01-01' group by fingerprint) order by date desc;")
sth.execute ; rows = sth.fetch_all

puts "# Old keys used for uploads to Debian"

rows.each do |r|
  next if not (oldkeys + oldkeys_dm).include?(r['fingerprint'])
  puts "#{r['date']} #{r['fingerprint']} #{r['signed_by_name']} (#{r['source']})"
end
sth.finish