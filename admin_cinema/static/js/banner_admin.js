function isFormEmpty(formItem) {
  const urlInput = formItem.querySelector('input[name$="-url_banner"]');
  const textInput = formItem.querySelector('input[name$="-text_banner"]');
  const fileInput = formItem.querySelector('input[type="file"]');

  const urlEmpty = !urlInput || urlInput.value.trim() === '';
  const textEmpty = !textInput || textInput.value.trim() === '';
  const fileEmpty = !fileInput || fileInput.value === '';

  return urlEmpty && textEmpty && fileEmpty;
}

function getActiveForms(formsetContainer) {
  return Array.from(formsetContainer.querySelectorAll('.form-item'))
    .filter(formItem => {
      const deleteCheckbox = formItem.querySelector('input[type=checkbox][name$="-DELETE"]');
      return deleteCheckbox && !deleteCheckbox.checked && formItem.style.display !== 'none';
    });
}

function hideDeletedForms() {
  document.querySelectorAll('.delete-cross').forEach(function(cross) {
    cross.onclick = function () {
      const formItem = this.closest('.form-item');

      let formsetContainer = formItem.parentElement;
      while (formsetContainer && !formsetContainer.style.display.includes('flex')) {
        formsetContainer = formsetContainer.parentElement;
      }

      const deleteCheckbox = formItem.querySelector('input[type=checkbox][name$="-DELETE"]');
      const activeForms = getActiveForms(formsetContainer);

      if (activeForms.length === 1 && isFormEmpty(activeForms[0])) {
        alert('Последняя пустая форма не может быть удалена.');
        return;
      }

      deleteCheckbox.checked = true;
      formItem.style.display = 'none';
    };
  });
}

function addForm(prefix) {
  const totalForms = document.querySelector(`#id_${prefix}-TOTAL_FORMS`);
  const formCount = parseInt(totalForms.value);
  const formContainer = document.querySelector(`#${prefix}-form div[style*="display: flex"]`);
  const emptyFormTemplate = document.getElementById(`${prefix}-empty-form`).innerHTML;

  const newDiv = document.createElement('div');
  newDiv.innerHTML = emptyFormTemplate.replace(/__prefix__/g, formCount);
  formContainer.insertBefore(newDiv.firstElementChild, formContainer.querySelector('.add-button'));

  totalForms.value = formCount + 1;
  hideDeletedForms();
}

document.addEventListener('DOMContentLoaded', hideDeletedForms);
// === Предпросмотр загружаемой картинки ===
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('input[type="file"][accept^="image"]').forEach(function (input) {
    input.addEventListener('change', function (event) {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = function (e) {
        let img = input.closest('.image-container').querySelector('img');
        if (!img) {
          img = document.createElement('img');
          img.style.maxWidth = '100%';
          img.style.maxHeight = '100px';
          img.style.marginTop = '5px';
          input.closest('.image-container').prepend(img);
        }
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  });
});