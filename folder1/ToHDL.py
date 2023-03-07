#!python3
import sys
import os
import shutil
import re

print("1")
for file_name in ["fdd_800m"]:
    #while os.path.exists(file_name)==False:
        #print('file not found,input again!')
        #sys.exit()
    file_pt=open(file_name)
    print("1")
    content=file_pt.readlines()	#读取脚本文件，存储到content
    file_pt.close()
    lut_list=[]
    index=0
    #需要修改为SPIRead的命令列表
    change_list={
                "ReadPartNumber"    :   ["SPIRead\t037\t08\t","// ReadPartNumber"],
                "WAIT\t1"   :   ["SPIRead\t3FF\t01\t","// waits 1 ms"],
                "WAIT\t20"  :   ["SPIRead\t3FF\t14\t","// waits 20 ms"],
                "WAIT_CALDONE\tBBPLL,2000":["SPIRead\t05E\t80\t","// Wait for BBPLL to lock, Timeout 2sec, Max BBPLL VCO Cal Time: 345.600 us (Done when 0x05E[7]==1)"],
                "SPIRead\t05E"  :   ["SPIRead\t05E\t80\t","// Check BBPLL locked status  (0x05E[7]==1 is locked)"],
                "SPIRead\t247"  :   ["SPIRead\t247\t02\t","// Check RX RF PLL lock status (0x247[1]==1 is locked)"],
                "SPIRead\t287"  :   ["SPIRead\t287\t02\t","// Check TX RF PLL lock status (0x287[1]==1 is locked)"],
                "SPIRead\t1EB"	:	["SPIRead\t1EB\t00\t","// Read RxBBF C3 MSB"],
                "SPIRead\t1EC"	:	["SPIRead\t1EC\t00\t","// Read RxBBF C3 LSB"],
                "SPIRead\t1E6"	:	["SPIRead\t1E6\t00\t","// Read RxBBF R3"],
                "SPIRead\t0A3"	:	["SPIRead\t0A3\t00\t","// Masked Read:  Read lower 6 bits, overwrite [7:6] below"],
                "WAIT_CALDONE\tRXCP"    :   ["SPIRead\t244\t80\t","// Wait for RXCP cal to complete.Done when 0x244[7]==1"],
                "WAIT_CALDONE\tTXCP"    :   ["SPIRead\t284\t80\t","// Wait for TXCP cal to complete.Done when 0x284[7]==1"],
                "WAIT_CALDONE\tRXFILTER"    :   ["SPIRead\t016\t80\t","// Wait for RX filter to tune.Done when 0x016[7]==0"],
                "WAIT_CALDONE\tTXFILTER"    :   ["SPIRead\t016\t40\t","// Wait for TX filter to tune.Done when 0x016[6]==0"],
                "WAIT_CALDONE\tBBDC"    :   ["SPIRead\t016\t01\t","// Wait for BBDC cal to complete. Done when 0x016[0]==0"],
                "WAIT_CALDONE\tRFDC"    :   ["SPIRead\t016\t02\t","// Wait for RFDC cal to complete. Done when 0x016[1]==0"],
                "WAIT_CALDONE\tTXQUAD"  :   ["SPIRead\t016\t10\t","// Wait for TX Quad cal to complete. Done when 0x016[4]==0"],
                "WAIT_CALDONE\tRXQUAD"  :   ["SPIRead\t016\t20\t","// Wait for RX Quad cal to complete. Done when 0x016[5]==0"]
               }
    #将所有命令转换为SPIWrite和SPIRead命令
    for i in range(len(content)):
        content[i]=content[i].strip()
        for j,v in change_list.items():
            if j in content[i]:
                content[i]=v[0]+v[1]
    #消除文件中无用的脚本命令行和空白行，仅保留SPIWrite，SPIRead以及注释行开头的内容
    content_new=[]
    for i in content:
        for j in ["SPIRead","SPIWrite","//"]:
            if i.startswith(j):
                content_new.append(i)
    #生成verilog格式的代码
    print("1")
    for i in content_new:
        if i.startswith('SPIRead'):           #将SPIRead开头的命令行转换为verilog格式的代码
            lut_list.append("13'd"+str(index).ljust(4,' ')+":"+file_name+"={1'b0,10'h"+i[8:11]+",8'h"+i[12:14]+"};"+i[14:])   
            index=index+1      
        elif i.startswith('SPIWrite'):        #将SPIWrite开头的命令行转换为verilog格式的代码
            lut_list.append("13'd"+str(index).ljust(4,' ')+":"+file_name+"={1'b1,10'h"+i[9:12]+",8'h"+i[13:15]+"};"+i[15:])
            index=index+1                                         
        else:                                 #保留注释
            lut_list.append(i)
    #修改寄存器15C的值
    lut_list.append("13'd"+str(index).ljust(4,' ')+":"+file_name+"={1'b1,10'h15C,8'h02};\t// Power Measurement Duration")
    index=index+1    
    #脚本中未添加从ALERT状态到TX/RX/FDD状态的命令，这里手动添加,先读10h014的值，和0x60位与后写回去
    regex=re.compile(file_name+"={1'b1,10'h014,8'h[0-9,A-F]{2}}",re.I)
    print("1")
    for i in lut_list:
        mo=regex.search(i)
        if mo!=None:
            tmp_data=mo.group()
            break       
    tmp_data=int(tmp_data[-3:-1],16)
    tmp_data=str(hex(tmp_data|0x60))
    tmp_data=tmp_data[2:4].upper()
    lut_list.append("//************************************************************")
    lut_list.append("//Manually add:Force RX and TX on")
    lut_list.append("//************************************************************")
    lut_list.append("13'd"+str(index).ljust(4,' ')+":"+file_name+"={1'b1,10'h014,8'h"+tmp_data+"};\t// Set Force rx and tx State bit")
    index=index+1
    #添加结尾命令
    lut_list.append("13'd"+str(index).ljust(4,' ')+":"+file_name+"={1'b0,10'h3FF,8'hFF};\t// end of command")
    #将命令列表写入到头文件
    print("1")
    file_pt=open(file_name+'.v','w')
    file_pt.write("function [18:0] "+file_name+";\n")
    file_pt.write("input [12:0] index;\n")
    file_pt.write("\tbegin\n")
    file_pt.write("\t\tcase(index)\n")
    for i in lut_list:
        file_pt.write('\t\t\t'+i+'\n')
    file_pt.write("\t\tendcase\n")
    file_pt.write("\tend\n")
    file_pt.write("endfunction\n")
    file_pt.close()
    print('work done!')
sys.exit()
