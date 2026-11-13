document.querySelectorAll('.toast').forEach(el=>setTimeout(()=>{el.style.opacity='0';setTimeout(()=>el.remove(),300)},4500));
