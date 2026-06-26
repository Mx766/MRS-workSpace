$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open('d:\translation\original\rhBMP-2 (DWP431) Repeat-Dose Toxicity_Rat_2 weeks.pdf')
$outpath = 'd:\translation\output\toxicity\rhbmp2_word_import.docx'
$doc.SaveAs2([ref]$outpath, [ref]16)
$doc.Close()
$word.Quit()
Write-Output "Word import completed: $outpath"
